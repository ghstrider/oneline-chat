import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getFullUrl } from '../config/api';

interface ShareSettings {
  title: string;
  description?: string;
  is_public: boolean;
  expires_at?: string;
}

interface ShareResponse {
  share_token: string;
  share_url: string;
  title: string;
  is_public: boolean;
  expires_at?: string;
  created_at: string;
}

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  chatId: string;
  chatTitle: string;
}

export const ShareModal: React.FC<ShareModalProps> = ({
  isOpen,
  onClose,
  chatId,
  chatTitle
}) => {
  const { isAuthenticated } = useAuth();
  const [shareSettings, setShareSettings] = useState<ShareSettings>({
    title: chatTitle || 'Untitled Chat',
    description: '',
    is_public: true,
    expires_at: ''
  });
  const [shareInfo, setShareInfo] = useState<ShareResponse | null>(null);
  const [isSharing, setIsSharing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState(false);

  // Update title when chatTitle prop changes
  useEffect(() => {
    if (chatTitle) {
      setShareSettings(prev => ({ ...prev, title: chatTitle }));
    }
  }, [chatTitle]);

  // Load existing share info when modal opens
  useEffect(() => {
    if (isOpen && isAuthenticated && chatId) {
      loadShareInfo();
    }
  }, [isOpen, isAuthenticated, chatId]);

  const loadShareInfo = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(getFullUrl(`/api/v1/chat/${chatId}/share`), {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('sessionToken')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data: ShareResponse = await response.json();
        setShareInfo(data);
        setShareSettings({
          title: data.title,
          description: '',
          is_public: data.is_public,
          expires_at: data.expires_at || ''
        });
        setIsSharing(true);
      } else if (response.status === 404) {
        // Chat is not shared
        setIsSharing(false);
        setShareInfo(null);
      } else {
        throw new Error('Failed to load share info');
      }
    } catch (error) {
      console.error('Error loading share info:', error);
      setError('Failed to load share information');
    } finally {
      setIsLoading(false);
    }
  };

  const handleShare = async () => {
    if (!isAuthenticated) {
      setError('You must be logged in to share chats');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(getFullUrl(`/api/v1/chat/${chatId}/share`), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('sessionToken')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          title: shareSettings.title,
          description: shareSettings.description || null,
          is_public: shareSettings.is_public,
          expires_at: shareSettings.expires_at || null
        })
      });

      if (!response.ok) {
        throw new Error('Failed to share chat');
      }

      const data: ShareResponse = await response.json();
      setShareInfo(data);
      setIsSharing(true);
    } catch (error) {
      console.error('Error sharing chat:', error);
      setError('Failed to share chat. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUnshare = async () => {
    if (!isAuthenticated) return;

    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(getFullUrl(`/api/v1/chat/${chatId}/share`), {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('sessionToken')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to unshare chat');
      }

      setShareInfo(null);
      setIsSharing(false);
    } catch (error) {
      console.error('Error unsharing chat:', error);
      setError('Failed to unshare chat. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyLink = async () => {
    if (!shareInfo?.share_url) return;
    
    try {
      await navigator.clipboard.writeText(shareInfo.share_url);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (error) {
      console.error('Failed to copy link:', error);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Share Chat
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {!isAuthenticated ? (
            <div className="text-center py-8">
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                You must be logged in to share chats.
              </p>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                Close
              </button>
            </div>
          ) : (
            <>
              {isLoading && (
                <div className="flex justify-center py-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
                </div>
              )}

              {error && (
                <div className="mb-4 p-3 bg-red-100 dark:bg-red-900/20 border border-red-300 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400 text-sm">
                  {error}
                </div>
              )}

              {!isSharing ? (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Title
                    </label>
                    <input
                      type="text"
                      value={shareSettings.title}
                      onChange={(e) => setShareSettings(prev => ({ ...prev, title: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter a title for the shared chat"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Description (optional)
                    </label>
                    <textarea
                      value={shareSettings.description}
                      onChange={(e) => setShareSettings(prev => ({ ...prev, description: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Optional description"
                      rows={3}
                    />
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="is_public"
                      checked={shareSettings.is_public}
                      onChange={(e) => setShareSettings(prev => ({ ...prev, is_public: e.target.checked }))}
                      className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                    />
                    <label htmlFor="is_public" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                      Make publicly accessible
                    </label>
                  </div>

                  <div className="flex space-x-3 pt-4">
                    <button
                      onClick={onClose}
                      className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleShare}
                      disabled={isLoading || !shareSettings.title.trim()}
                      className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      Share
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                    <div className="flex items-center">
                      <svg className="w-5 h-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-sm text-green-800 dark:text-green-300 font-medium">
                        Chat is shared publicly
                      </span>
                    </div>
                  </div>

                  {shareInfo && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Share Link
                      </label>
                      <div className="flex">
                        <input
                          type="text"
                          value={shareInfo.share_url}
                          readOnly
                          className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-l-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                        />
                        <button
                          onClick={handleCopyLink}
                          className="px-3 py-2 bg-blue-500 text-white border border-blue-500 rounded-r-lg hover:bg-blue-600 transition-colors"
                        >
                          {copySuccess ? (
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                          ) : (
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                          )}
                        </button>
                      </div>
                      {copySuccess && (
                        <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                          Link copied to clipboard!
                        </p>
                      )}
                    </div>
                  )}

                  <div className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
                    <p>Title: {shareInfo?.title}</p>
                    <p>Created: {shareInfo?.created_at ? new Date(shareInfo.created_at).toLocaleDateString() : 'Unknown'}</p>
                  </div>

                  <div className="flex space-x-3 pt-4">
                    <button
                      onClick={onClose}
                      className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                      Close
                    </button>
                    <button
                      onClick={handleUnshare}
                      disabled={isLoading}
                      className="flex-1 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      Unshare
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};