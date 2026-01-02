/**
 * Resume Tailor Extension - Background Service Worker
 * Handles background tasks and manages extension state
 */

// Configuration
const CONFIG = {
  API_BASE_URL: 'http://localhost:5000',
  CHECK_INTERVAL: 30000, // 30 seconds
};

// State
let serverStatus = {
  connected: false,
  lastCheck: null,
  error: null,
};

/**
 * Check server health
 */
async function checkServerHealth() {
  try {
    const response = await fetch(`${CONFIG.API_BASE_URL}/health`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    
    if (response.ok) {
      const data = await response.json();
      serverStatus = {
        connected: true,
        lastCheck: new Date().toISOString(),
        data: data,
        error: null,
      };
      
      // Update badge to show connected status
      updateBadge(true);
    } else {
      throw new Error(`Server returned ${response.status}`);
    }
  } catch (error) {
    serverStatus = {
      connected: false,
      lastCheck: new Date().toISOString(),
      error: error.message,
    };
    
    // Update badge to show disconnected status
    updateBadge(false);
  }
  
  return serverStatus;
}

/**
 * Update extension badge based on status
 */
function updateBadge(connected) {
  if (connected) {
    chrome.action.setBadgeText({ text: '' });
    chrome.action.setBadgeBackgroundColor({ color: '#10b981' });
    chrome.action.setTitle({ title: 'Resume Tailor - Connected' });
  } else {
    chrome.action.setBadgeText({ text: '!' });
    chrome.action.setBadgeBackgroundColor({ color: '#ef4444' });
    chrome.action.setTitle({ title: 'Resume Tailor - Server Offline' });
  }
}

/**
 * Handle messages from popup and content scripts
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  switch (request.action) {
    case 'getServerStatus':
      sendResponse(serverStatus);
      break;
      
    case 'checkServer':
      checkServerHealth().then(sendResponse);
      return true; // Async response
      
    case 'jobDetected':
      // Job page detected by content script
      handleJobDetected(request.data, sender.tab);
      sendResponse({ received: true });
      break;
      
    case 'tailorResume':
      tailorResume(request.data).then(sendResponse);
      return true; // Async response
      
    default:
      sendResponse({ error: 'Unknown action' });
  }
  
  return false;
});

/**
 * Handle job page detection
 */
function handleJobDetected(data, tab) {
  console.log('[Resume Tailor] Job detected:', {
    title: data.jobTitle,
    company: data.company,
    url: data.url,
    descriptionLength: data.jobDescription?.length,
  });
  
  // Store the detected job for quick access
  chrome.storage.local.set({
    lastDetectedJob: {
      ...data,
      tabId: tab?.id,
      detectedAt: new Date().toISOString(),
    },
  });
  
  // Could show notification or update badge here
}

/**
 * Tailor resume via API
 */
async function tailorResume(data) {
  try {
    const response = await fetch(`${CONFIG.API_BASE_URL}/tailor`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `Server error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('[Resume Tailor] Tailor error:', error);
    return { error: error.message };
  }
}

/**
 * Create context menu items
 */
function setupContextMenu() {
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: 'tailorWithSelection',
      title: 'Tailor Resume with Selected Text',
      contexts: ['selection'],
    });
    
    chrome.contextMenus.create({
      id: 'extractFromPage',
      title: 'Extract Job Description from Page',
      contexts: ['page'],
    });
  });
}

/**
 * Handle context menu clicks
 */
chrome.contextMenus.onClicked.addListener((info, tab) => {
  switch (info.menuItemId) {
    case 'tailorWithSelection':
      if (info.selectionText) {
        // Open popup with selected text
        chrome.storage.local.set({
          pendingJobDescription: info.selectionText,
        }, () => {
          chrome.action.openPopup();
        });
      }
      break;
      
    case 'extractFromPage':
      // Trigger extraction in content script
      chrome.tabs.sendMessage(tab.id, { action: 'extractJobInfo' }, (response) => {
        if (response && response.jobDescription) {
          chrome.storage.local.set({
            pendingJobDescription: response.jobDescription,
            pendingJobTitle: response.jobTitle,
            pendingCompany: response.company,
          }, () => {
            chrome.action.openPopup();
          });
        }
      });
      break;
  }
});

/**
 * Handle extension installation
 */
chrome.runtime.onInstalled.addListener((details) => {
  console.log('[Resume Tailor] Extension installed:', details.reason);
  
  // Setup context menu
  setupContextMenu();
  
  // Initial server check
  checkServerHealth();
  
  // Show welcome page on install
  if (details.reason === 'install') {
    chrome.tabs.create({
      url: 'welcome.html',
    }).catch(() => {
      // Welcome page might not exist
    });
  }
});

/**
 * Handle extension startup
 */
chrome.runtime.onStartup.addListener(() => {
  console.log('[Resume Tailor] Extension started');
  setupContextMenu();
  checkServerHealth();
});

// Periodic server health check
setInterval(checkServerHealth, CONFIG.CHECK_INTERVAL);

// Initial check
checkServerHealth();
