import React from 'react';
import { usePWA } from '../hooks/usePWA';
import { WifiOff, Wifi } from 'lucide-react';

const OfflineIndicator = () => {
  const { isOnline } = usePWA();

  if (isOnline) {
    return null; // Don't show anything when online
  }

  return (
    <div className="fixed top-0 left-0 right-0 bg-yellow-500 text-white px-4 py-2 text-center text-sm font-medium z-50 shadow-lg">
      <div className="flex items-center justify-center space-x-2">
        <WifiOff className="w-4 h-4" />
        <span>You're offline • Showing cached content</span>
      </div>
    </div>
  );
};

export default OfflineIndicator;