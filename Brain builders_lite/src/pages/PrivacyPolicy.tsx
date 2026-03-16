import { Link } from "react-router-dom";
import { LegalLayout } from "@/components/LegalLayout";

const PrivacyPolicy = () => (
  <LegalLayout title="Privacy Policy" lastUpdated="February 26, 2026">
    <p className="lead">
      Brain Bulders (&quot;we,&quot; &quot;us,&quot; or &quot;our&quot;) operates the platform at gcreators.me. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our mentorship platform.
    </p>

    <h2>1. Information We Collect</h2>
    <h3>1.1 Information You Provide</h3>
    <ul>
      <li><strong>Account data:</strong> Email address, name, password (hashed), profile details (goals, skill level, preferred language, timezone)</li>
      <li><strong>Mentor profiles:</strong> Bio, expertise, pricing, availability, profile photos</li>
      <li><strong>Communications:</strong> Messages with mentors, questions submitted, video responses</li>
      <li><strong>Payment data:</strong> Processed by Stripe; we do not store full card numbers</li>
    </ul>

    <h3>1.2 Information Collected Automatically</h3>
    <ul>
      <li><strong>Usage data:</strong> Pages visited, features used, session duration</li>
      <li><strong>Device data:</strong> Browser type, IP address, approximate location</li>
      <li><strong>Cookies and similar technologies:</strong> See our <Link to="/cookie-policy" className="text-primary underline hover:no-underline">Cookie Policy</Link></li>
    </ul>

    <h2>2. How We Use Your Information</h2>
    <ul>
      <li>Provide and operate the platform (mentor matching, bookings, messaging, purchases)</li>
      <li>Process payments via Stripe</li>
      <li>Send transactional emails (confirmations, reminders, notifications)</li>
      <li>Improve our services and develop new features</li>
      <li>Provide AI-powered features (mentor recommendations, avatar chat)</li>
      <li>Comply with legal obligations and enforce our Terms of Service</li>
    </ul>

    <h2>3. Legal Basis for Processing (GDPR)</h2>
    <p>If you are in the European Economic Area (EEA) or UK:</p>
    <ul>
      <li><strong>Contract:</strong> Processing necessary to provide our services</li>
      <li><strong>Legitimate interests:</strong> Improving services, security, analytics</li>
      <li><strong>Consent:</strong> Marketing communications, optional features</li>
      <li><strong>Legal obligation:</strong> Tax, fraud prevention, regulatory compliance</li>
    </ul>

    <h2>4. Third-Party Services</h2>
    <p>We use the following service providers who may process your data:</p>
    <ul>
      <li><strong>Supabase:</strong> Authentication, database, file storage (EU/US data centers)</li>
      <li><strong>Stripe:</strong> Payment processing (see <a href="https://stripe.com/privacy" target="_blank" rel="noopener noreferrer" className="text-primary underline hover:no-underline">Stripe&apos;s Privacy Policy</a>)</li>
      <li><strong>OpenAI:</strong> AI features (embeddings, chat) when you use avatar consultations</li>
      <li><strong>Google:</strong> Calendar integration (if you connect your calendar)</li>
      <li><strong>Resend / Email providers:</strong> Transactional and notification emails</li>
    </ul>

    <h2>5. Data Retention</h2>
    <ul>
      <li>Account and profile data: Retained while your account is active; deleted or anonymized upon account closure</li>
      <li>Messages and questions: Retained for service delivery and support</li>
      <li>Payment records: Retained as required by tax and financial regulations (typically 7 years)</li>
      <li>Logs and analytics: Typically 12–24 months</li>
    </ul>

    <h2>6. Your Rights (GDPR &amp; CCPA)</h2>
    <p>You have the right to:</p>
    <ul>
      <li><strong>Access:</strong> Request a copy of your personal data</li>
      <li><strong>Rectification:</strong> Correct inaccurate or incomplete data</li>
      <li><strong>Erasure:</strong> Request deletion of your data (&quot;right to be forgotten&quot;)</li>
      <li><strong>Portability:</strong> Receive your data in a machine-readable format</li>
      <li><strong>Object:</strong> Object to processing based on legitimate interests</li>
      <li><strong>Restrict:</strong> Restrict processing in certain circumstances</li>
      <li><strong>Withdraw consent:</strong> Where processing is based on consent</li>
    </ul>
    <p>To exercise these rights, contact us at the email below. You may also lodge a complaint with your local data protection authority.</p>

    <h2>7. Data Security</h2>
    <p>We implement technical and organizational measures to protect your data, including encryption in transit (TLS) and at rest, access controls, and secure authentication. No system is completely secure; we encourage strong passwords and prompt reporting of any suspected breach.</p>

    <h2>8. International Transfers</h2>
    <p>Your data may be transferred to and processed in countries outside your residence. We ensure appropriate safeguards (e.g., Standard Contractual Clauses) where required by law.</p>

    <h2>9. Children</h2>
    <p>Our services are not directed to individuals under 16. We do not knowingly collect data from children. If you believe we have collected data from a child, please contact us.</p>

    <h2>10. Changes</h2>
    <p>We may update this Privacy Policy from time to time. We will notify you of material changes via email or a notice on the platform. Continued use after changes constitutes acceptance.</p>

    <h2>11. Contact</h2>
    <p>
      For privacy-related inquiries: <a href="mailto:privacy@gcreators.me" className="text-primary underline hover:no-underline">privacy@gcreators.me</a>
      <br />
      Brain Bulders · Founded by Vita Shafinska
    </p>
  </LegalLayout>
);

export default PrivacyPolicy;
