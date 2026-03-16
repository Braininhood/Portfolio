import { Link } from "react-router-dom";
import { LegalLayout } from "@/components/LegalLayout";

const TermsOfService = () => (
  <LegalLayout title="Terms of Service" lastUpdated="February 26, 2026">
    <p className="lead">
      These Terms of Service (&quot;Terms&quot;) govern your use of Brain Bulders (&quot;Platform,&quot; &quot;we,&quot; &quot;us&quot;) at gcreators.me. By creating an account or using the Platform, you agree to these Terms.
    </p>

    <h2>1. Acceptance of Terms</h2>
    <p>By accessing or using Brain Bulders, you agree to be bound by these Terms and our <Link to="/privacy-policy" className="text-primary underline hover:no-underline">Privacy Policy</Link>. If you do not agree, do not use the Platform.</p>

    <h2>2. Description of Service</h2>
    <p>Brain Bulders is a mentorship platform that connects learners with mentors. We provide:</p>
    <ul>
      <li>Mentor discovery and profile browsing</li>
      <li>Booking of consultation sessions</li>
      <li>Purchase of digital products from mentors</li>
      <li>Messaging between learners and mentors</li>
      <li>AI-powered features (recommendations, avatar consultations)</li>
    </ul>
    <p>We act as an intermediary. Mentors are independent service providers; we do not guarantee the quality, accuracy, or legality of mentor content or services.</p>

    <h2>3. Account Registration</h2>
    <ul>
      <li>You must be at least 16 years old and provide accurate, complete information</li>
      <li>You are responsible for maintaining the confidentiality of your account credentials</li>
      <li>You must notify us promptly of any unauthorized access</li>
    </ul>

    <h2>4. User Conduct</h2>
    <p>You agree not to:</p>
    <ul>
      <li>Violate any applicable laws or regulations</li>
      <li>Infringe intellectual property, privacy, or other rights of others</li>
      <li>Harass, abuse, defame, or harm other users</li>
      <li>Transmit malware, spam, or harmful content</li>
      <li>Attempt to gain unauthorized access to our systems or other accounts</li>
      <li>Use the Platform for any fraudulent or illegal purpose</li>
    </ul>
    <p>We reserve the right to suspend or terminate accounts that violate these Terms.</p>

    <h2>5. Mentor Terms</h2>
    <p>If you register as a mentor:</p>
    <ul>
      <li>You represent that you have the expertise and authority to offer your services</li>
      <li>You are responsible for your content, pricing, and delivery of services</li>
      <li>You must comply with Stripe Connect terms for receiving payments</li>
      <li>You grant us a license to display your profile and content on the Platform</li>
    </ul>

    <h2>6. Payments and Refunds</h2>
    <ul>
      <li>Payments are processed by Stripe. By purchasing, you agree to Stripe&apos;s terms</li>
      <li>Prices are set by mentors; we may charge a platform fee</li>
      <li>Refund policies are determined by individual mentors unless otherwise stated</li>
      <li>Chargebacks and disputes are handled in accordance with Stripe and applicable law</li>
    </ul>

    <h2>7. Intellectual Property</h2>
    <p>Brain Bulders and its branding, design, and technology are owned by us. Mentors retain ownership of their content. By posting content, you grant us a non-exclusive, worldwide, royalty-free license to use, display, and distribute it in connection with the Platform.</p>

    <h2>8. Disclaimers</h2>
    <p>THE PLATFORM IS PROVIDED &quot;AS IS&quot; AND &quot;AS AVAILABLE.&quot; WE DISCLAIM ALL WARRANTIES, EXPRESS OR IMPLIED, INCLUDING MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. WE DO NOT GUARANTEE UNINTERRUPTED, ERROR-FREE, OR SECURE OPERATION.</p>

    <h2>9. Limitation of Liability</h2>
    <p>TO THE MAXIMUM EXTENT PERMITTED BY LAW, WE SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR LOSS OF PROFITS, DATA, OR GOODWILL, ARISING FROM YOUR USE OF THE PLATFORM. OUR TOTAL LIABILITY SHALL NOT EXCEED THE AMOUNT YOU PAID US IN THE TWELVE MONTHS PRECEDING THE CLAIM.</p>

    <h2>10. Indemnification</h2>
    <p>You agree to indemnify and hold harmless Brain Bulders, its affiliates, and their officers, directors, employees, and agents from any claims, damages, losses, or expenses (including legal fees) arising from your use of the Platform, your content, or your violation of these Terms.</p>

    <h2>11. Termination</h2>
    <p>We may suspend or terminate your account at any time for violation of these Terms or for any other reason. You may close your account at any time. Upon termination, your right to use the Platform ceases; provisions that by their nature should survive (e.g., disclaimers, limitation of liability) will survive.</p>

    <h2>12. Governing Law</h2>
    <p>These Terms are governed by the laws of the jurisdiction in which Brain Bulders operates, without regard to conflict of law principles. Any disputes shall be resolved in the courts of that jurisdiction.</p>

    <h2>13. Changes</h2>
    <p>We may modify these Terms at any time. We will notify you of material changes via email or a notice on the Platform. Continued use after changes constitutes acceptance. If you do not agree, you must stop using the Platform.</p>

    <h2>14. Contact</h2>
    <p>
      For questions about these Terms: <a href="mailto:legal@gcreators.me" className="text-primary underline hover:no-underline">legal@gcreators.me</a>
      <br />
      Brain Bulders · Founded by Vita Shafinska
    </p>
  </LegalLayout>
);

export default TermsOfService;
