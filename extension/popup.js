/**
 * Resume Tailor Extension - Popup Script
 * Handles UI interactions and communication with the backend API
 */

// Configuration
const CONFIG = {
  API_BASE_URL: 'http://localhost:5000',
  MIN_JD_LENGTH: 50,
};

// DOM Elements
const elements = {
  statusIndicator: document.getElementById('statusIndicator'),
  connectionStatus: document.getElementById('connectionStatus'),
  jobDescription: document.getElementById('jobDescription'),
  charCount: document.getElementById('charCount'),
  extractBtn: document.getElementById('extractBtn'),
  toggleOptional: document.getElementById('toggleOptional'),
  optionalSection: document.getElementById('optionalSection'),
  optionalContent: document.getElementById('optionalContent'),
  jobTitle: document.getElementById('jobTitle'),
  company: document.getElementById('company'),
  keywords: document.getElementById('keywords'),
  formatPdf: document.getElementById('formatPdf'),
  formatDocx: document.getElementById('formatDocx'),
  tailorBtn: document.getElementById('tailorBtn'),
  btnText: document.getElementById('btnText'),
  spinner: document.getElementById('spinner'),
  resultsSection: document.getElementById('resultsSection'),
  closeResults: document.getElementById('closeResults'),
  scoreCircle: document.getElementById('scoreCircle'),
  scoreValue: document.getElementById('scoreValue'),
  keywordsList: document.getElementById('keywordsList'),
  suggestionsList: document.getElementById('suggestionsList'),
  downloadLinks: document.getElementById('downloadLinks'),
  errorMessage: document.getElementById('errorMessage'),
  errorText: document.getElementById('errorText'),
};

// State
let isServerConnected = false;
let isProcessing = false;

/**
 * Initialize the popup
 */
async function init() {
  // Check server connection
  await checkServerConnection();
  
  // Set up event listeners
  setupEventListeners();
  
  // Load saved state
  loadSavedState();
  
  // Update UI state
  updateButtonState();
}

/**
 * Check if the backend server is running
 */
async function checkServerConnection() {
  try {
    const response = await fetch(`${CONFIG.API_BASE_URL}/health`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    
    if (response.ok) {
      const data = await response.json();
      isServerConnected = data.status === 'healthy' || data.status === 'degraded';
      updateConnectionUI(true, data);
    } else {
      throw new Error('Server returned error');
    }
  } catch (error) {
    console.error('Server connection failed:', error);
    isServerConnected = false;
    updateConnectionUI(false);
  }
}

/**
 * Update connection status UI
 */
function updateConnectionUI(connected, data = null) {
  const { statusIndicator, connectionStatus } = elements;
  
  if (connected) {
    statusIndicator.classList.add('connected');
    statusIndicator.classList.remove('disconnected');
    statusIndicator.title = 'Server connected';
    
    if (data && data.status === 'degraded') {
      connectionStatus.textContent = 'Connected (some features may be limited)';
      connectionStatus.className = 'connection-status show warning';
    } else {
      connectionStatus.className = 'connection-status';
    }
  } else {
    statusIndicator.classList.add('disconnected');
    statusIndicator.classList.remove('connected');
    statusIndicator.title = 'Server disconnected';
    
    connectionStatus.innerHTML = `
      Server not running. Start it with:<br>
      <code style="font-size: 11px; background: #fee; padding: 2px 4px; border-radius: 3px;">
        cd backend && python app.py
      </code>
    `;
    connectionStatus.className = 'connection-status show error';
  }
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
  // Job description input
  elements.jobDescription.addEventListener('input', () => {
    updateCharCount();
    updateButtonState();
    saveState();
  });
  
  // Extract button
  elements.extractBtn.addEventListener('click', extractFromPage);
  
  // Toggle optional section
  elements.toggleOptional.addEventListener('click', () => {
    elements.optionalSection.classList.toggle('open');
  });
  
  // Optional fields
  elements.jobTitle.addEventListener('input', saveState);
  elements.company.addEventListener('input', saveState);
  elements.keywords.addEventListener('input', saveState);
  
  // Format checkboxes
  elements.formatPdf.addEventListener('change', updateButtonState);
  elements.formatDocx.addEventListener('change', updateButtonState);
  
  // Tailor button
  elements.tailorBtn.addEventListener('click', tailorResume);
  
  // Close results
  elements.closeResults.addEventListener('click', () => {
    elements.resultsSection.classList.remove('show');
  });
  
  // Status indicator click to retry connection
  elements.statusIndicator.addEventListener('click', checkServerConnection);
}

/**
 * Update character count display
 */
function updateCharCount() {
  const count = elements.jobDescription.value.length;
  elements.charCount.textContent = count.toLocaleString();
}

/**
 * Update button state based on form validity
 */
function updateButtonState() {
  const jdLength = elements.jobDescription.value.trim().length;
  const hasFormat = elements.formatPdf.checked || elements.formatDocx.checked;
  const isValid = jdLength >= CONFIG.MIN_JD_LENGTH && hasFormat && isServerConnected && !isProcessing;
  
  elements.tailorBtn.disabled = !isValid;
}

/**
 * Extract job description from the current page
 */
async function extractFromPage() {
  try {
    showExtractingState(true);
    hideError();
    
    // Get the active tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab) {
      showError('No active tab found');
      showExtractingState(false);
      return;
    }
    
    // Check if we can access the tab
    if (!tab.url || tab.url.startsWith('chrome://') || tab.url.startsWith('chrome-extension://') || tab.url.startsWith('about:')) {
      showError('Cannot extract from this page. Navigate to a job posting first.');
      showExtractingState(false);
      return;
    }
    
    // Execute extraction directly on the page
    try {
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: extractJobDataFromPage,
      });
      
      showExtractingState(false);
      
      if (results && results[0] && results[0].result) {
        handleExtractionResult(results[0].result);
      } else {
        showError('Could not extract job description. Please copy and paste manually.');
      }
    } catch (scriptError) {
      console.error('Script execution error:', scriptError);
      showExtractingState(false);
      showError('Cannot access this page. Try copying the job description manually.');
    }
    
  } catch (error) {
    console.error('Extraction error:', error);
    showError('Failed to extract from page. Try copying manually.');
    showExtractingState(false);
  }
}

/**
 * This function runs in the context of the web page
 */
function extractJobDataFromPage() {
  const result = {
    jobDescription: '',
    jobTitle: '',
    company: '',
    url: window.location.href,
  };
  
  // =============================================
  // JOB DESCRIPTION EXTRACTION
  // =============================================
  
  const jdSelectors = [
    // LinkedIn
    '.jobs-description__content',
    '.jobs-description-content__text',
    '.jobs-box__html-content',
    '.jobs-description',
    '#job-details',
    '.job-view-layout jobs-description',
    
    // Indeed
    '#jobDescriptionText',
    '.jobsearch-jobDescriptionText',
    '.jobsearch-JobComponent-description',
    
    // Glassdoor
    '.jobDescriptionContent',
    '[data-test="jobDescription"]',
    '.desc.job-description',
    '#JobDescriptionContainer',
    
    // ZipRecruiter
    '.job_description',
    '.jobDescriptionSection',
    
    // Lever
    '.posting-requirements',
    '[data-qa="job-description"]',
    '.section-wrapper.page-full-width',
    '.content .section',
    
    // Greenhouse
    '#content .job-post-content',
    '#app_body',
    '.job__description',
    
    // Workday
    '[data-automation-id="jobPostingDescription"]',
    '.job-description',
    
    // SmartRecruiters
    '.job-sections',
    '.jobad-description',
    '.job-description-container',
    
    // Generic patterns (try these last)
    '[class*="job-description"]',
    '[class*="jobDescription"]',
    '[class*="job_description"]',
    '[id*="job-description"]',
    '[id*="jobDescription"]',
    '[id*="job_description"]',
    '.description',
    '#description',
    '[class*="description"]',
    '.job-details',
    '.posting-requirements',
    'article',
    '[role="article"]',
  ];
  
  // Try each selector
  for (const selector of jdSelectors) {
    try {
      const element = document.querySelector(selector);
      if (element) {
        const text = element.innerText.trim();
        if (text.length > 100) {
          result.jobDescription = text;
          break;
        }
      }
    } catch (e) {
      // Skip invalid selectors
    }
  }
  
  // Fallback: try main content area
  if (!result.jobDescription) {
    const mainSelectors = ['main', '[role="main"]', '#main-content', '#main', '.main-content', '.main'];
    for (const selector of mainSelectors) {
      try {
        const element = document.querySelector(selector);
        if (element) {
          const text = element.innerText.trim();
          if (text.length > 200) {
            result.jobDescription = text;
            break;
          }
        }
      } catch (e) {
        // Skip
      }
    }
  }
  
  // Last resort: get body text (limited)
  if (!result.jobDescription || result.jobDescription.length < 100) {
    const bodyText = document.body.innerText.trim();
    if (bodyText.length > 200) {
      result.jobDescription = bodyText.substring(0, 15000);
    }
  }
  
  // =============================================
  // JOB TITLE EXTRACTION
  // =============================================
  
  const titleSelectors = [
    // LinkedIn
    '.jobs-unified-top-card__job-title',
    '.job-details-jobs-unified-top-card__job-title',
    '.t-24.job-details-jobs-unified-top-card__job-title',
    '.topcard__title',
    
    // Indeed
    '.jobsearch-JobInfoHeader-title',
    'h1[data-testid="jobsearch-JobInfoHeader-title"]',
    '.icl-u-xs-mb--xs.icl-u-xs-mt--none',
    
    // Glassdoor
    '[data-test="jobTitle"]',
    '.e1tk4kwz4',
    
    // Lever
    '.posting-headline h2',
    
    // Generic
    'h1.job-title',
    'h1.jobTitle',
    '.job-title',
    '.jobTitle',
    '[class*="job-title"]',
    '[class*="jobTitle"]',
    'h1',
  ];
  
  for (const selector of titleSelectors) {
    try {
      const element = document.querySelector(selector);
      if (element) {
        const text = element.innerText.trim();
        // Job title should be reasonable length
        if (text.length > 2 && text.length < 150) {
          result.jobTitle = text;
          break;
        }
      }
    } catch (e) {
      // Skip
    }
  }
  
  // =============================================
  // COMPANY NAME EXTRACTION
  // =============================================
  
  const companySelectors = [
    // LinkedIn
    '.jobs-unified-top-card__company-name a',
    '.jobs-unified-top-card__company-name',
    '.job-details-jobs-unified-top-card__company-name',
    '.topcard__org-name-link',
    
    // Indeed
    '[data-testid="inlineHeader-companyName"]',
    '[data-testid="inlineHeader-companyName"] a',
    '.jobsearch-InlineCompanyRating-companyHeader a',
    '.icl-u-lg-mr--sm a',
    
    // Glassdoor
    '[data-test="employer-name"]',
    '.e1tk4kwz1',
    
    // Generic
    '.company-name a',
    '.company-name',
    '.companyName a',
    '.companyName',
    '[class*="company-name"]',
    '[class*="companyName"]',
    '.employer-name',
    '.hiring-company',
    '[class*="employer"]',
  ];
  
  for (const selector of companySelectors) {
    try {
      const element = document.querySelector(selector);
      if (element) {
        const text = element.innerText.trim();
        if (text.length > 1 && text.length < 100) {
          result.company = text;
          break;
        }
      }
    } catch (e) {
      // Skip
    }
  }
  
  return result;
}

/**
 * Handle extraction result
 */
function handleExtractionResult(data) {
  const { jobDescription, jobTitle, company } = data;
  
  if (jobDescription && jobDescription.length >= 50) {
    // Success - populate form
    elements.jobDescription.value = jobDescription;
    updateCharCount();
    
    if (jobTitle) {
      elements.jobTitle.value = jobTitle;
    }
    
    if (company) {
      elements.company.value = company;
    }
    
    // Open optional section if we found details
    if (jobTitle || company) {
      elements.optionalSection.classList.add('open');
    }
    
    updateButtonState();
    saveState();
    
    // Show success feedback
    showSuccess(`Extracted ${jobDescription.length.toLocaleString()} characters`);
  } else {
    showError('Could not find job description on this page. Try copying manually.');
  }
}

/**
 * Show extracting state on button
 */
function showExtractingState(extracting) {
  const btn = elements.extractBtn;
  if (extracting) {
    btn.innerHTML = `
      <svg class="spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 12a9 9 0 11-6.219-8.56"></path>
      </svg>
      Extracting...
    `;
    btn.disabled = true;
    btn.style.opacity = '0.7';
  } else {
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>
      Extract
    `;
    btn.disabled = false;
    btn.style.opacity = '1';
  }
}

/**
 * Show success message briefly
 */
function showSuccess(message) {
  const statusEl = elements.connectionStatus;
  statusEl.textContent = '✓ ' + message;
  statusEl.className = 'connection-status show success';
  
  setTimeout(() => {
    if (isServerConnected) {
      statusEl.className = 'connection-status';
    }
  }, 3000);
}

/**
 * Tailor the resume using the API
 */
async function tailorResume() {
  if (isProcessing || !isServerConnected) return;
  
  isProcessing = true;
  setLoadingState(true);
  hideError();
  elements.resultsSection.classList.remove('show');
  
  try {
    // Prepare request data
    const outputFormats = [];
    if (elements.formatPdf.checked) outputFormats.push('pdf');
    if (elements.formatDocx.checked) outputFormats.push('docx');
    
    const keywords = elements.keywords.value
      .split(',')
      .map(k => k.trim())
      .filter(k => k.length > 0);
    
    const requestBody = {
      job_description: elements.jobDescription.value.trim(),
      job_title: elements.jobTitle.value.trim() || null,
      company: elements.company.value.trim() || null,
      output_formats: outputFormats,
      emphasis_keywords: keywords.length > 0 ? keywords : null,
    };
    
    // Make API request
    const response = await fetch(`${CONFIG.API_BASE_URL}/tailor`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `Server error: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Display results
    displayResults(data);
    
  } catch (error) {
    console.error('Tailor error:', error);
    showError(error.message || 'Failed to tailor resume. Please try again.');
  } finally {
    isProcessing = false;
    setLoadingState(false);
  }
}

/**
 * Display the tailoring results
 */
function displayResults(data) {
  const { resultsSection, scoreCircle, scoreValue, keywordsList, suggestionsList, downloadLinks } = elements;
  
  // Show results section
  resultsSection.classList.add('show');
  
  // Update ATS score
  if (data.ats_score !== null && data.ats_score !== undefined) {
    const score = data.ats_score;
    scoreValue.textContent = score;
    scoreCircle.style.strokeDasharray = `${score}, 100`;
    
    // Update color based on score
    if (score >= 80) {
      scoreCircle.style.stroke = '#10b981'; // Green
    } else if (score >= 60) {
      scoreCircle.style.stroke = '#f59e0b'; // Yellow
    } else {
      scoreCircle.style.stroke = '#ef4444'; // Red
    }
  } else {
    scoreValue.textContent = '--';
    scoreCircle.style.strokeDasharray = '0, 100';
  }
  
  // Update keywords
  keywordsList.innerHTML = '';
  if (data.keywords_matched && data.keywords_matched.length > 0) {
    data.keywords_matched.forEach(keyword => {
      const tag = document.createElement('span');
      tag.className = 'keyword-tag';
      tag.textContent = keyword;
      keywordsList.appendChild(tag);
    });
    document.getElementById('keywordsSection').style.display = 'block';
  } else {
    document.getElementById('keywordsSection').style.display = 'none';
  }
  
  // Update suggestions
  suggestionsList.innerHTML = '';
  if (data.suggestions && data.suggestions.length > 0) {
    data.suggestions.forEach(suggestion => {
      const li = document.createElement('li');
      li.textContent = suggestion;
      suggestionsList.appendChild(li);
    });
    document.getElementById('suggestionsSection').style.display = 'block';
  } else {
    document.getElementById('suggestionsSection').style.display = 'none';
  }
  
  // Update download links
  downloadLinks.innerHTML = '';
  if (data.files_generated && data.files_generated.length > 0) {
    data.files_generated.forEach(file => {
      const link = document.createElement('a');
      link.className = 'download-link';
      link.href = `${CONFIG.API_BASE_URL}${file.download_url}`;
      link.target = '_blank';
      link.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="7 10 12 15 17 10"></polyline>
          <line x1="12" y1="15" x2="12" y2="3"></line>
        </svg>
        <span>${file.filename}</span>
        <span style="color: var(--text-muted); font-size: 11px; margin-left: auto;">
          ${formatFileSize(file.size_bytes)}
        </span>
      `;
      downloadLinks.appendChild(link);
    });
    document.getElementById('downloadsSection').style.display = 'block';
  } else {
    document.getElementById('downloadsSection').style.display = 'none';
  }
}

/**
 * Format file size for display
 */
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

/**
 * Set loading state
 */
function setLoadingState(loading) {
  if (loading) {
    elements.tailorBtn.classList.add('loading');
    elements.tailorBtn.disabled = true;
  } else {
    elements.tailorBtn.classList.remove('loading');
    updateButtonState();
  }
}

/**
 * Show error message
 */
function showError(message) {
  elements.errorText.textContent = message;
  elements.errorMessage.classList.add('show');
}

/**
 * Hide error message
 */
function hideError() {
  elements.errorMessage.classList.remove('show');
}

/**
 * Save state to storage
 */
function saveState() {
  const state = {
    jobDescription: elements.jobDescription.value,
    jobTitle: elements.jobTitle.value,
    company: elements.company.value,
    keywords: elements.keywords.value,
  };
  
  chrome.storage.local.set({ resumeTailorState: state });
}

/**
 * Load saved state from storage
 */
function loadSavedState() {
  chrome.storage.local.get(['resumeTailorState'], (result) => {
    if (result.resumeTailorState) {
      const state = result.resumeTailorState;
      elements.jobDescription.value = state.jobDescription || '';
      elements.jobTitle.value = state.jobTitle || '';
      elements.company.value = state.company || '';
      elements.keywords.value = state.keywords || '';
      updateCharCount();
      updateButtonState();
    }
  });
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init);
