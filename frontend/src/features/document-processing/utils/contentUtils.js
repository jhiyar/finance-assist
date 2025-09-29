/**
 * Utility functions for cleaning and formatting chunk content
 */

/**
 * Clean chunk content by removing binary/encoded characters and artifacts
 * @param {string} content - Raw chunk content
 * @returns {string} - Cleaned content
 */
export const cleanChunkContent = (content) => {
  if (!content) return '';
  
  // Clean the content to remove binary/encoded characters
  let cleanedContent = content;
  
  // Remove or replace common binary/encoding artifacts
  cleanedContent = cleanedContent
    // Remove null bytes and control characters
    .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '')
    // Remove common PDF artifacts and extended ASCII
    .replace(/[\x80-\x9F]/g, '')
    // Replace multiple spaces with single space
    .replace(/\s+/g, ' ')
    // Remove excessive line breaks
    .replace(/\n\s*\n\s*\n/g, '\n\n')
    // Trim whitespace
    .trim();
  
  // If content is mostly non-printable characters, show a warning
  const printableChars = cleanedContent.replace(/[^\x20-\x7E\n\r\t]/g, '').length;
  const totalChars = cleanedContent.length;
  const printableRatio = totalChars > 0 ? printableChars / totalChars : 0;
  
  if (printableRatio < 0.5 && totalChars > 50) {
    return `[Warning: Content appears to contain binary or encoded data]\n\n${cleanedContent.substring(0, 500)}...`;
  }
  
  return cleanedContent;
};

/**
 * Format chunk content for display with truncation
 * @param {string} content - Chunk content
 * @param {number} maxLength - Maximum length for display
 * @returns {string} - Formatted content
 */
export const formatChunkContent = (content, maxLength = 2000) => {
  const cleaned = cleanChunkContent(content);
  return cleaned.length > maxLength ? cleaned.substring(0, maxLength) + '...' : cleaned;
};

/**
 * Check if content appears to be binary or encoded
 * @param {string} content - Content to check
 * @returns {boolean} - True if content appears to be binary/encoded
 */
export const isBinaryContent = (content) => {
  if (!content) return false;
  
  const printableChars = content.replace(/[^\x20-\x7E\n\r\t]/g, '').length;
  const totalChars = content.length;
  const printableRatio = totalChars > 0 ? printableChars / totalChars : 0;
  
  return printableRatio < 0.5 && totalChars > 50;
};

/**
 * Extract readable text from potentially corrupted content
 * @param {string} content - Raw content
 * @returns {string} - Extracted readable text
 */
export const extractReadableText = (content) => {
  if (!content) return '';
  
  // Try to extract only printable characters
  const readableChars = content.match(/[\x20-\x7E\n\r\t]/g);
  
  if (!readableChars) return '[No readable text found]';
  
  const readableText = readableChars.join('');
  
  // Clean up the text
  return readableText
    .replace(/\s+/g, ' ')
    .replace(/\n\s*\n\s*\n/g, '\n\n')
    .trim();
};
