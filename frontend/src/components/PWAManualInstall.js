import React, { useState } from 'react';
import { Download, Smartphone, Monitor, X } from 'lucide-react';

const PWAManualInstall = () => {
  const [isVisible, setIsVisible] = useState(
    localStorage.getItem('pwa-manual-dismissed') !== 'true'
  );

  if (!isVisible) return null;

  const handleDismiss = () => {
    setIsVisible(false);
    localStorage.setItem('pwa-manual-dismissed', 'true');
  };

  const instructions = {
    android: [
      "1. Tap the browser menu (⋮) in Chrome/Edge",
      "2. Tap 'Add to Home Screen' or 'Install App'", 
      "3. Confirm installation",
      "4. App icon appears on home screen"
    ],
    ios: [
      "1. Tap the Share button (□↑) in Safari",
      "2. Scroll and tap 'Add to Home Screen'",
      "3. Edit name if desired, tap 'Add'",
      "4. App icon appears on home screen"
    ],
    desktop: [
      "1. Look for install icon (⬇) in address bar",
      "2. Or browser menu → 'Install On-the-Cheap'",
      "3. Confirm installation", 
      "4. App appears in Start Menu/Applications"
    ]
  };

  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:max-w-md z-50">
      <div className="bg-white border-2 border-orange-500 rounded-lg shadow-xl p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Download className="w-5 h-5 text-orange-600" />
            <h3 className="font-semibold text-gray-900 text-sm">
              📱 Install as App
            </h3>
          </div>
          <button
            onClick={handleDismiss}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <p className="text-xs text-gray-600 mb-4">
          Install On-the-Cheap as an app for faster access and offline viewing!
        </p>

        <div className="space-y-3">
          {/* Android Instructions */}
          <div className="border rounded p-3 bg-green-50">
            <div className="flex items-center mb-2">
              <Smartphone className="w-4 h-4 text-green-600 mr-2" />
              <span className="font-medium text-green-800 text-xs">Android (Chrome/Edge)</span>
            </div>
            <ol className="text-xs text-green-700 space-y-1">
              {instructions.android.map((step, idx) => (
                <li key={idx} className="text-xs">{step}</li>
              ))}
            </ol>
          </div>

          {/* iOS Instructions */}
          <div className="border rounded p-3 bg-blue-50">
            <div className="flex items-center mb-2">
              <Smartphone className="w-4 h-4 text-blue-600 mr-2" />
              <span className="font-medium text-blue-800 text-xs">iPhone/iPad (Safari)</span>
            </div>
            <ol className="text-xs text-blue-700 space-y-1">
              {instructions.ios.map((step, idx) => (
                <li key={idx} className="text-xs">{step}</li>
              ))}
            </ol>
          </div>

          {/* Desktop Instructions */}
          <div className="border rounded p-3 bg-purple-50">
            <div className="flex items-center mb-2">
              <Monitor className="w-4 h-4 text-purple-600 mr-2" />
              <span className="font-medium text-purple-800 text-xs">Desktop</span>
            </div>
            <ol className="text-xs text-purple-700 space-y-1">
              {instructions.desktop.map((step, idx) => (
                <li key={idx} className="text-xs">{step}</li>
              ))}
            </ol>
          </div>
        </div>

        <div className="mt-4 text-center">
          <button
            onClick={handleDismiss}
            className="text-xs text-gray-500 hover:text-gray-700"
          >
            I'll install later
          </button>
        </div>
      </div>
    </div>
  );
};

export default PWAManualInstall;