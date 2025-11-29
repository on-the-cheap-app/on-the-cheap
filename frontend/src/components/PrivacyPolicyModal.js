import React from 'react';

const PrivacyPolicyModal = ({ onClose }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-500 to-red-500 text-white p-6 flex justify-between items-center flex-shrink-0">
          <div>
            <h2 className="text-2xl font-bold">Privacy Policy</h2>
            <p className="text-orange-100">Last updated: November 29, 2025</p>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:text-orange-200 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 p-6 overflow-y-auto">
          <div className="space-y-6">
            
            <section>
              <h3 className="text-xl font-bold text-gray-900 mb-3">1. Introduction</h3>
              <p className="text-gray-700 leading-relaxed">
                Welcome to On the Cheap ("we," "our," or "us"). We respect your privacy and are committed to protecting your personal data. 
                This privacy policy explains how we collect, use, disclose, and safeguard your information when you use our mobile application 
                and website (collectively, the "Service").
              </p>
            </section>

            <section>
              <h3 className="text-xl font-bold text-gray-900 mb-3">2. Information We Collect</h3>
              
              <h4 className="text-lg font-semibold text-gray-900 mb-2 mt-3">2.1 Personal Information</h4>
              <p className="text-gray-700 mb-2">We may collect personal information that you provide to us, including:</p>
              <ul className="list-disc list-inside text-gray-700 space-y-1 ml-4">
                <li>Name and email address</li>
                <li>Location data (to show nearby restaurant specials)</li>
                <li>Payment information (processed securely through Stripe)</li>
                <li>Restaurant preferences and favorites</li>
              </ul>

              <h4 className="text-lg font-semibold text-gray-900 mb-2 mt-3">2.2 Usage Information</h4>
              <ul className="list-disc list-inside text-gray-700 space-y-1 ml-4">
                <li>Device information (type, operating system)</li>
                <li>Log data (IP address, browser type)</li>
                <li>Usage patterns</li>
                <li>Location information (with your permission)</li>
              </ul>
            </section>

            <section>
              <h3 className="text-xl font-bold text-gray-900 mb-3">3. How We Use Your Information</h3>
              <ul className="list-disc list-inside text-gray-700 space-y-1 ml-4">
                <li>Provide and improve our Service</li>
                <li>Show relevant restaurant specials near you</li>
                <li>Process payments and subscriptions</li>
                <li>Send notifications about saved specials</li>
                <li>Respond to customer service requests</li>
                <li>Analyze usage to improve experience</li>
                <li>Prevent fraud and address technical issues</li>
              </ul>
            </section>

            <section>
              <h3 className="text-xl font-bold text-gray-900 mb-3">4. Information Sharing</h3>
              <p className="text-gray-700 mb-2">We do not sell your personal information. We may share information with:</p>
              <ul className="list-disc list-inside text-gray-700 space-y-1 ml-4">
                <li>Service providers (Stripe, cloud hosting)</li>
                <li>Restaurants (anonymized usage data)</li>
                <li>Legal authorities when required by law</li>
              </ul>
            </section>

            <section>
              <h3 className="text-xl font-bold text-gray-900 mb-3">5. Data Security</h3>
              <p className="text-gray-700 leading-relaxed">
                We implement appropriate security measures to protect your personal information, including encryption and secure servers. 
                However, no method of transmission over the internet is 100% secure.
              </p>
            </section>

            <section>
              <h3 className="text-xl font-bold text-gray-900 mb-3">6. Your Rights</h3>
              <ul className="list-disc list-inside text-gray-700 space-y-1 ml-4">
                <li><strong>Access:</strong> Request a copy of your personal information</li>
                <li><strong>Correction:</strong> Update inaccurate information</li>
                <li><strong>Deletion:</strong> Request deletion of your account and data</li>
                <li><strong>Opt-out:</strong> Unsubscribe from marketing communications</li>
                <li><strong>Location:</strong> Disable location services in settings</li>
              </ul>
            </section>

            <section>
              <h3 className="text-xl font-bold text-gray-900 mb-3">7. Children's Privacy</h3>
              <p className="text-gray-700 leading-relaxed">
                Our Service is not intended for children under 13. We do not knowingly collect information from children under 13.
              </p>
            </section>

            <section>
              <h3 className="text-xl font-bold text-gray-900 mb-3">8. Changes to This Policy</h3>
              <p className="text-gray-700 leading-relaxed">
                We may update this privacy policy from time to time. We will notify you of changes by posting the new policy on this page.
              </p>
            </section>

            <section>
              <h3 className="text-xl font-bold text-gray-900 mb-3">9. Contact Us</h3>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-gray-700"><strong>On the Cheap</strong></p>
                <p className="text-gray-700">Email: privacy@onthecheapapp.com</p>
                <p className="text-gray-700">Website: https://www.onthecheapapp.com</p>
              </div>
            </section>

            <section className="border-t pt-4">
              <h3 className="text-xl font-bold text-gray-900 mb-3">California & GDPR Rights</h3>
              <p className="text-gray-700 leading-relaxed">
                California residents and EU users have additional rights under CCPA and GDPR respectively, including rights to access, 
                delete, and control how their data is used. Contact us to exercise these rights.
              </p>
            </section>

          </div>
        </div>

        {/* Footer */}
        <div className="border-t p-4 flex-shrink-0">
          <button
            onClick={onClose}
            className="w-full py-2 px-4 bg-orange-500 hover:bg-orange-600 text-white font-semibold rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default PrivacyPolicyModal;
