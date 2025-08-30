import React, { useState } from 'react';
import { usePWA } from '../hooks/usePWA';
import { Download, X, Smartphone } from 'lucide-react';

const PWAInstallBanner = () => {
  const { isInstallable, isInstalled, installPWA } = usePWA();
  const [isDismissed, setIsDismissed] = useState(
    localStorage.getItem('pwa-install-dismissed') === 'true'
  );

  // Debug PWA state
  console.log('🔍 PWA Banner Debug:', { isInstallable, isInstalled, isDismissed });

  // Don't show if already installed, not installable, or dismissed
  if (isInstalled || !isInstallable || isDismissed) {
    return null;
  }

  const handleInstall = async () => {
    const success = await installPWA();
    if (success) {
      setIsDismissed(true);
    }
  };

  const handleDismiss = () => {
    setIsDismissed(true);
    localStorage.setItem('pwa-install-dismissed', 'true');
  };

  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:max-w-sm z-50">
      <div className="bg-gradient-to-r from-orange-500 to-red-500 text-white p-4 rounded-lg shadow-lg border border-orange-400">
        <div className="flex items-start space-x-3">
          <Smartphone className="w-6 h-6 mt-1 flex-shrink-0" />
          
          <div className="flex-1">
            <h3 className="font-semibold text-sm mb-1">
              📱 Install On-the-Cheap
            </h3>
            <p className="text-sm opacity-90 mb-3">
              Get faster access, offline viewing, and push notifications for restaurant specials!
            </p>
            
            <div className="flex space-x-2">
              <button
                onClick={handleInstall}
                className="bg-white text-orange-600 px-3 py-1.5 rounded text-sm font-medium hover:bg-gray-100 transition-colors flex items-center"
              >
                <Download className="w-4 h-4 mr-1" />
                Install
              </button>
              
              <button
                onClick={handleDismiss}
                className="bg-orange-600 bg-opacity-20 text-white px-3 py-1.5 rounded text-sm hover:bg-opacity-30 transition-colors"
              >
                Later
              </button>
            </div>
          </div>
          
          <button
            onClick={handleDismiss}
            className="text-white hover:text-gray-200 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default PWAInstallBanner;