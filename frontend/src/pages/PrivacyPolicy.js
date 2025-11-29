import React from 'react';
import { useNavigate } from 'react-router-dom';

const PrivacyPolicy = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <button
            onClick={() => navigate('/')}
            className="text-orange-500 hover:text-orange-600 flex items-center mb-4"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Home
          </button>
          <h1 className="text-3xl font-bold text-gray-900">Privacy Policy</h1>
          <p className="text-gray-600 mt-2">Last updated: November 29, 2025</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-md p-8 space-y-8">
          
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">1. Introduction</h2>
            <p className="text-gray-700 leading-relaxed">
              Welcome to On the Cheap ("we," "our," or "us"). We respect your privacy and are committed to protecting your personal data. 
              This privacy policy explains how we collect, use, disclose, and safeguard your information when you use our mobile application 
              and website (collectively, the "Service").
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">2. Information We Collect</h2>
            
            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-4">2.1 Personal Information</h3>
            <p className="text-gray-700 leading-relaxed mb-3">
              We may collect personal information that you provide to us, including:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Name and email address (for account creation)</li>
              <li>Location data (to show nearby restaurant specials)</li>
              <li>Payment information (processed securely through Stripe)</li>
              <li>Restaurant preferences and favorites</li>
              <li>Profile information you choose to provide</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-4">2.2 Usage Information</h3>
            <p className="text-gray-700 leading-relaxed mb-3">
              We automatically collect certain information when you use our Service:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Device information (type, operating system, unique identifiers)</li>
              <li>Log data (IP address, browser type, pages visited)</li>
              <li>Usage patterns (features used, time spent, interactions)</li>
              <li>Location information (with your permission)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">3. How We Use Your Information</h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              We use the information we collect to:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Provide, maintain, and improve our Service</li>
              <li>Show you relevant restaurant specials and coupons near you</li>
              <li>Process payments and subscription transactions</li>
              <li>Send you notifications about specials you've saved</li>
              <li>Respond to your comments, questions, and customer service requests</li>
              <li>Analyze usage patterns to improve user experience</li>
              <li>Detect, prevent, and address technical issues or fraudulent activity</li>
              <li>Comply with legal obligations</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">4. Information Sharing and Disclosure</h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              We do not sell your personal information. We may share your information only in the following circumstances:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li><strong>With Restaurants:</strong> We share anonymized usage data with restaurant partners to help them understand customer preferences</li>
              <li><strong>Service Providers:</strong> We use third-party services (Stripe for payments, cloud hosting) that may access your data to perform services on our behalf</li>
              <li><strong>Legal Requirements:</strong> We may disclose information if required by law or to protect our rights</li>
              <li><strong>Business Transfers:</strong> If we're involved in a merger or acquisition, your information may be transferred</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">5. Data Security</h2>
            <p className="text-gray-700 leading-relaxed">
              We implement appropriate technical and organizational measures to protect your personal information against unauthorized access, 
              alteration, disclosure, or destruction. This includes encryption of sensitive data, secure servers, and regular security audits. 
              However, no method of transmission over the internet is 100% secure, and we cannot guarantee absolute security.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">6. Your Rights and Choices</h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              You have the following rights regarding your personal information:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li><strong>Access:</strong> Request a copy of the personal information we hold about you</li>
              <li><strong>Correction:</strong> Update or correct inaccurate information</li>
              <li><strong>Deletion:</strong> Request deletion of your account and personal data</li>
              <li><strong>Opt-out:</strong> Unsubscribe from marketing communications</li>
              <li><strong>Location:</strong> Disable location services through your device settings</li>
              <li><strong>Data Portability:</strong> Request your data in a portable format</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">7. Children's Privacy</h2>
            <p className="text-gray-700 leading-relaxed">
              Our Service is not intended for children under 13 years of age. We do not knowingly collect personal information from children under 13. 
              If you are a parent or guardian and believe your child has provided us with personal information, please contact us, and we will delete such information.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">8. Third-Party Links</h2>
            <p className="text-gray-700 leading-relaxed">
              Our Service may contain links to third-party websites or services. We are not responsible for the privacy practices of these third parties. 
              We encourage you to review their privacy policies before providing any personal information.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">9. Changes to This Privacy Policy</h2>
            <p className="text-gray-700 leading-relaxed">
              We may update this privacy policy from time to time. We will notify you of any changes by posting the new policy on this page and 
              updating the "Last updated" date. You are advised to review this privacy policy periodically for any changes.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">10. Contact Us</h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              If you have questions or concerns about this privacy policy or our data practices, please contact us:
            </p>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-gray-700"><strong>On the Cheap</strong></p>
              <p className="text-gray-700">Email: privacy@onthecheapapp.com</p>
              <p className="text-gray-700">Website: https://www.onthecheapapp.com</p>
            </div>
          </section>

          <section className="border-t pt-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">California Privacy Rights</h2>
            <p className="text-gray-700 leading-relaxed">
              If you are a California resident, you have additional rights under the California Consumer Privacy Act (CCPA), including 
              the right to know what personal information we collect, the right to delete your information, and the right to opt-out of 
              the sale of your information (which we do not do). To exercise these rights, please contact us using the information above.
            </p>
          </section>

          <section className="border-t pt-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">GDPR Rights (European Users)</h2>
            <p className="text-gray-700 leading-relaxed">
              If you are located in the European Economic Area (EEA), you have rights under the General Data Protection Regulation (GDPR), 
              including the right to access, rectify, erase, restrict processing, object to processing, and data portability. 
              You also have the right to lodge a complaint with a supervisory authority.
            </p>
          </section>

        </div>
      </div>
    </div>
  );
};

export default PrivacyPolicy;
