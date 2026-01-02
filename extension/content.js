/**
 * Resume Tailor Extension - Content Script
 * Runs in the context of web pages to extract job descriptions
 */

(function() {
  'use strict';

  // Prevent multiple injections
  if (window.resumeTailorInjected) return;
  window.resumeTailorInjected = true;

  console.log('[Resume Tailor] Content script loaded');

  /**
   * Site-specific extraction configurations
   */
  const SITE_CONFIGS = {
    'linkedin.com': {
      jobDescription: [
        '.jobs-description__content',
        '.jobs-box__html-content',
        '.jobs-description',
        '#job-details',
      ],
      jobTitle: [
        '.jobs-unified-top-card__job-title',
        '.job-details-jobs-unified-top-card__job-title',
        'h1.t-24',
      ],
      company: [
        '.jobs-unified-top-card__company-name',
        '.job-details-jobs-unified-top-card__company-name',
        '.jobs-unified-top-card__subtitle-primary-grouping a',
      ],
    },
    'indeed.com': {
      jobDescription: [
        '#jobDescriptionText',
        '.jobsearch-jobDescriptionText',
        '.jobsearch-JobComponent-description',
      ],
      jobTitle: [
        '.jobsearch-JobInfoHeader-title',
        'h1[data-testid="jobsearch-JobInfoHeader-title"]',
        '.icl-u-xs-mb--xs',
      ],
      company: [
        '[data-testid="inlineHeader-companyName"]',
        '.jobsearch-InlineCompanyRating-companyHeader',
        '.icl-u-lg-mr--sm',
      ],
    },
    'glassdoor.com': {
      jobDescription: [
        '.jobDescriptionContent',
        '[data-test="jobDescription"]',
        '.desc',
      ],
      jobTitle: [
        '[data-test="jobTitle"]',
        '.css-1vg6q84',
        'h1',
      ],
      company: [
        '[data-test="employer-name"]',
        '.css-87uc0g',
        '.employerName',
      ],
    },
    'ziprecruiter.com': {
      jobDescription: [
        '.job_description',
        '.jobDescriptionSection',
      ],
      jobTitle: [
        '.job_title',
        'h1.text-2xl',
      ],
      company: [
        '.hiring_company',
        '.job_company_name',
      ],
    },
    'lever.co': {
      jobDescription: [
        '.posting-requirements',
        '[data-qa="job-description"]',
        '.section-wrapper',
      ],
      jobTitle: [
        '.posting-headline h2',
        'h1',
      ],
      company: [
        '.posting-headline .company-name',
        '.main-header-logo',
      ],
    },
    'greenhouse.io': {
      jobDescription: [
        '#content',
        '.job-post-content',
        '#app_body',
      ],
      jobTitle: [
        '.app-title',
        'h1.heading',
      ],
      company: [
        '.company-name',
        '.logo-wrapper',
      ],
    },
  };

  /**
   * Generic selectors for unknown sites
   */
  const GENERIC_SELECTORS = {
    jobDescription: [
      '[class*="job-description"]',
      '[class*="jobDescription"]',
      '[class*="job_description"]',
      '[id*="job-description"]',
      '[id*="jobDescription"]',
      '[id*="job_description"]',
      '[class*="description"]',
      '[class*="posting"]',
      '[class*="details"]',
      'article',
      'main',
      '[role="main"]',
    ],
    jobTitle: [
      'h1',
      '[class*="job-title"]',
      '[class*="jobTitle"]',
      '[class*="job_title"]',
      '[class*="position"]',
      '[class*="role-name"]',
    ],
    company: [
      '[class*="company-name"]',
      '[class*="companyName"]',
      '[class*="company_name"]',
      '[class*="employer"]',
      '[class*="organization"]',
    ],
  };

  /**
   * Get the current site's hostname
   */
  function getSiteKey() {
    const hostname = window.location.hostname.toLowerCase();
    
    for (const site of Object.keys(SITE_CONFIGS)) {
      if (hostname.includes(site)) {
        return site;
      }
    }
    
    return null;
  }

  /**
   * Extract text using a list of selectors
   */
  function extractWithSelectors(selectors, minLength = 0, maxLength = Infinity) {
    for (const selector of selectors) {
      try {
        const element = document.querySelector(selector);
        if (element) {
          const text = element.innerText.trim();
          if (text.length >= minLength && text.length <= maxLength) {
            return text;
          }
        }
      } catch (e) {
        // Invalid selector, skip
      }
    }
    return '';
  }

  /**
   * Clean and normalize extracted text
   */
  function cleanText(text) {
    if (!text) return '';
    
    return text
      .replace(/\s+/g, ' ')  // Normalize whitespace
      .replace(/\n{3,}/g, '\n\n')  // Limit consecutive newlines
      .trim();
  }

  /**
   * Extract job information from the current page
   */
  function extractJobInfo() {
    const siteKey = getSiteKey();
    const config = siteKey ? SITE_CONFIGS[siteKey] : GENERIC_SELECTORS;
    
    console.log(`[Resume Tailor] Extracting from: ${siteKey || 'generic site'}`);
    
    // Extract job description
    let jobDescription = extractWithSelectors(
      config.jobDescription,
      100,  // Minimum 100 characters
      50000  // Maximum 50k characters
    );
    
    // Fallback: try generic selectors if site-specific didn't work
    if (!jobDescription && siteKey) {
      jobDescription = extractWithSelectors(
        GENERIC_SELECTORS.jobDescription,
        100,
        50000
      );
    }
    
    // Extract job title
    let jobTitle = extractWithSelectors(
      config.jobTitle,
      3,   // Minimum 3 characters
      150  // Maximum 150 characters
    );
    
    if (!jobTitle && siteKey) {
      jobTitle = extractWithSelectors(GENERIC_SELECTORS.jobTitle, 3, 150);
    }
    
    // Extract company name
    let company = extractWithSelectors(
      config.company,
      2,   // Minimum 2 characters
      100  // Maximum 100 characters
    );
    
    if (!company && siteKey) {
      company = extractWithSelectors(GENERIC_SELECTORS.company, 2, 100);
    }
    
    // Clean up extracted data
    const result = {
      jobDescription: cleanText(jobDescription),
      jobTitle: cleanText(jobTitle),
      company: cleanText(company),
      url: window.location.href,
      extractedAt: new Date().toISOString(),
    };
    
    console.log('[Resume Tailor] Extracted:', {
      jdLength: result.jobDescription.length,
      jobTitle: result.jobTitle,
      company: result.company,
    });
    
    return result;
  }

  /**
   * Listen for messages from the popup
   */
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'extractJobInfo') {
      console.log('[Resume Tailor] Received extraction request');
      
      const result = extractJobInfo();
      sendResponse(result);
    }
    
    return true; // Keep message channel open for async response
  });

  /**
   * Highlight job description element (optional, for debugging)
   */
  function highlightElement(selector) {
    const element = document.querySelector(selector);
    if (element) {
      const originalBorder = element.style.border;
      element.style.border = '3px solid #2563eb';
      
      setTimeout(() => {
        element.style.border = originalBorder;
      }, 2000);
    }
  }

  // Auto-extract on page load and notify background script
  setTimeout(() => {
    const result = extractJobInfo();
    
    if (result.jobDescription.length > 100) {
      chrome.runtime.sendMessage({
        action: 'jobDetected',
        data: result,
      }).catch(() => {
        // Background script might not be ready
      });
    }
  }, 1500);

})();
