import React from 'react';
import { ArrowLeft, Mail, Phone, MapPin } from 'lucide-react';

const PartnerInfo = () => {
  return (
    <div className="min-h-screen bg-gradient-to-b from-amber-50 to-orange-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <a href="/" className="text-orange-500 hover:text-orange-600 flex items-center mb-4" data-testid="back-home-link">
            <ArrowLeft className="w-5 h-5 mr-2" />
            Back to Home
          </a>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900">Partner with Us</h1>
          <p className="text-gray-600 mt-2">Join On-the-Cheap and fill more seats</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Intro Section */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl sm:text-3xl font-bold text-orange-600 mb-4">
            Partner with On-the-Cheap & Fill More Seats
          </h2>
          <p className="text-gray-700 text-lg leading-relaxed">
            Join a data-driven platform that connects your restaurant with customers actively seeking great deals—backed by proven research expertise and strategic innovation.
          </p>
        </div>

        {/* Founder Section */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
            <span className="mr-2">👋</span> Meet the Founder
          </h3>
          
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
            <div className="bg-orange-50 rounded-lg p-4 text-center border border-orange-100">
              <div className="text-xs text-orange-600 font-semibold uppercase tracking-wide mb-1">Education</div>
              <div className="text-sm font-medium text-gray-900">PhD in Psychology</div>
            </div>
            <div className="bg-orange-50 rounded-lg p-4 text-center border border-orange-100">
              <div className="text-xs text-orange-600 font-semibold uppercase tracking-wide mb-1">Experience</div>
              <div className="text-sm font-medium text-gray-900">15+ Years Research</div>
            </div>
            <div className="bg-orange-50 rounded-lg p-4 text-center border border-orange-100">
              <div className="text-xs text-orange-600 font-semibold uppercase tracking-wide mb-1">Expertise</div>
              <div className="text-sm font-medium text-gray-900">Data Analytics</div>
            </div>
            <div className="bg-orange-50 rounded-lg p-4 text-center border border-orange-100">
              <div className="text-xs text-orange-600 font-semibold uppercase tracking-wide mb-1">Focus</div>
              <div className="text-sm font-medium text-gray-900">Consumer Behavior</div>
            </div>
          </div>
        </div>

        {/* Why Choose Us Section */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h3 className="text-xl font-bold text-gray-900 mb-6">Why Restaurant Owners Choose On-the-Cheap</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-gradient-to-br from-orange-50 to-amber-50 rounded-lg p-6 border border-orange-100">
              <div className="text-3xl mb-3">📊</div>
              <h4 className="font-bold text-gray-900 mb-2">Data-Driven Insights</h4>
              <p className="text-gray-600 text-sm">
                Built by a research scientist who understands consumer psychology and buying patterns. Get analytics that actually help you make smarter business decisions.
              </p>
            </div>
            
            <div className="bg-gradient-to-br from-orange-50 to-amber-50 rounded-lg p-6 border border-orange-100">
              <div className="text-3xl mb-3">💰</div>
              <h4 className="font-bold text-gray-900 mb-2">Fill Slow Times</h4>
              <p className="text-gray-600 text-sm">
                Attract customers during off-peak hours with targeted deals. Turn empty tables into revenue without sacrificing your prime-time profits.
              </p>
            </div>
            
            <div className="bg-gradient-to-br from-orange-50 to-amber-50 rounded-lg p-6 border border-orange-100">
              <div className="text-3xl mb-3">🎯</div>
              <h4 className="font-bold text-gray-900 mb-2">Reach Ready Buyers</h4>
              <p className="text-gray-600 text-sm">
                Connect with customers who are actively looking for dining deals right now—not passive browsers. These are motivated buyers ready to visit your restaurant.
              </p>
            </div>
            
            <div className="bg-gradient-to-br from-orange-50 to-amber-50 rounded-lg p-6 border border-orange-100">
              <div className="text-3xl mb-3">📈</div>
              <h4 className="font-bold text-gray-900 mb-2">Strategic Growth</h4>
              <p className="text-gray-600 text-sm">
                Leverage proven enrollment management strategies adapted from higher education. I've driven measurable growth at multiple institutions—now applied to restaurants.
              </p>
            </div>
          </div>
        </div>

        {/* Expertise Section */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h3 className="text-xl font-bold text-gray-900 mb-6">Built on Real Expertise, Not Just Tech</h3>
          
          <div className="space-y-4">
            <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg">
              <span className="text-xl">🔬</span>
              <div>
                <strong className="text-gray-900">Research Foundation</strong>
                <p className="text-gray-600 text-sm mt-1">Published researcher in peer-reviewed journals with expertise in human behavior and decision-making</p>
              </div>
            </div>
            
            <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg">
              <span className="text-xl">📊</span>
              <div>
                <strong className="text-gray-900">Data Analytics</strong>
                <p className="text-gray-600 text-sm mt-1">15+ years building data systems, analyzing trends, and turning insights into actionable strategies</p>
              </div>
            </div>
            
            <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg">
              <span className="text-xl">💼</span>
              <div>
                <strong className="text-gray-900">Strategic Planning</strong>
                <p className="text-gray-600 text-sm mt-1">Led enrollment growth and retention initiatives—proven methods now applied to customer acquisition</p>
              </div>
            </div>
            
            <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg">
              <span className="text-xl">🎯</span>
              <div>
                <strong className="text-gray-900">User Experience</strong>
                <p className="text-gray-600 text-sm mt-1">Professional UX researcher who understands what makes people click, engage, and convert</p>
              </div>
            </div>
          </div>
        </div>

        {/* Track Record Section */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h3 className="text-xl font-bold text-gray-900 mb-6">Proven Track Record of Driving Results</h3>
          
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <span className="text-green-500 text-lg">✅</span>
              <div>
                <strong className="text-gray-900">National Program Director:</strong>
                <span className="text-gray-600 ml-1">Led research and evaluation for 20+ city programs, implementing data systems that drove measurable improvements and secured continued funding</span>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <span className="text-green-500 text-lg">✅</span>
              <div>
                <strong className="text-gray-900">Institutional Research Director:</strong>
                <span className="text-gray-600 ml-1">Built enrollment forecasting models and strategic plans that helped institutions meet/exceed growth goals</span>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <span className="text-green-500 text-lg">✅</span>
              <div>
                <strong className="text-gray-900">User Experience Researcher:</strong>
                <span className="text-gray-600 ml-1">Conducted consumer research for tech companies, designing experiences that drive engagement and conversion</span>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <span className="text-green-500 text-lg">✅</span>
              <div>
                <strong className="text-gray-900">Multi-Venture Entrepreneur:</strong>
                <span className="text-gray-600 ml-1">Founder of Apollo Analytics (research consulting), Decisive Element Peak Performance (coaching), and On-the-Cheap (consumer tech)</span>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <span className="text-green-500 text-lg">✅</span>
              <div>
                <strong className="text-gray-900">Published Thought Leader:</strong>
                <span className="text-gray-600 ml-1">Multiple peer-reviewed publications on human behavior, creativity, and decision-making—research that informs platform design</span>
              </div>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="bg-gradient-to-r from-orange-500 to-amber-500 rounded-lg shadow-lg p-8 mb-8 text-center">
          <h3 className="text-2xl font-bold text-white mb-4">Ready to Fill More Seats?</h3>
          <p className="text-orange-100 mb-6">
            Join forward-thinking restaurants using data-driven strategies to increase traffic during slow times.
          </p>
          <a 
            href="mailto:info@onthecheapapp.com" 
            className="inline-block bg-white text-orange-600 font-bold py-3 px-8 rounded-lg hover:bg-orange-50 transition-colors shadow-md"
            data-testid="partner-cta-btn"
          >
            Partner With Us Today
          </a>
        </div>

        {/* Contact Info */}
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <p className="font-bold text-gray-900 text-lg">Dr. Scott R. Furtwengler</p>
          <p className="text-gray-600 mb-4">Founder & CEO, On-the-Cheap</p>
          
          <div className="flex flex-col sm:flex-row justify-center items-center gap-4 text-gray-600">
            <a href="mailto:info@onthecheapapp.com" className="flex items-center gap-2 text-orange-600 hover:text-orange-700">
              <Mail className="w-4 h-4" />
              info@onthecheapapp.com
            </a>
            <a href="tel:6189241145" className="flex items-center gap-2 text-orange-600 hover:text-orange-700">
              <Phone className="w-4 h-4" />
              618.924.1145
            </a>
            <span className="flex items-center gap-2">
              <MapPin className="w-4 h-4" />
              Nashville, Tennessee
            </span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-gray-100 py-6 text-center text-gray-500 text-sm">
        <p>© {new Date().getFullYear()} On-the-Cheap. All rights reserved.</p>
      </div>
    </div>
  );
};

export default PartnerInfo;
