import { Link } from "react-router-dom";
import { LegalLayout } from "@/components/LegalLayout";

const CookiePolicy = () => (
  <LegalLayout title="Cookie Policy" lastUpdated="February 26, 2026">
    <p className="lead">
      This Cookie Policy explains how Brain Bulders (&quot;we,&quot; &quot;us,&quot; or &quot;our&quot;) uses cookies and similar technologies when you use our platform at gcreators.me.
    </p>

    <h2>1. What Are Cookies?</h2>
    <p>Cookies are small text files stored on your device when you visit a website. They help the site remember your preferences, keep you signed in, and understand how you use the platform.</p>

    <h2>2. Cookies We Use</h2>

    <h3>2.1 Strictly Necessary Cookies</h3>
    <p>Required for the platform to function. Cannot be disabled.</p>
    <ul>
      <li><strong>Authentication:</strong> Keep you signed in (e.g., Supabase session cookies)</li>
      <li><strong>Security:</strong> Protect against cross-site request forgery (CSRF)</li>
      <li><strong>Load balancing:</strong> Distribute traffic across servers</li>
    </ul>

    <h3>2.2 Functional Cookies</h3>
    <p>Enable enhanced features and personalization.</p>
    <ul>
      <li><strong>Preferences:</strong> Language, timezone, theme (light/dark)</li>
      <li><strong>Session state:</strong> Cart, form data, navigation state</li>
    </ul>

    <h3>2.3 Analytics Cookies</h3>
    <p>Help us understand how visitors use the platform (pages viewed, features used). We use this to improve our services. Data is aggregated and anonymized where possible.</p>

    <h3>2.4 Third-Party Cookies</h3>
    <p>Some services we use may set their own cookies:</p>
    <ul>
      <li><strong>Stripe:</strong> Payment processing and fraud prevention</li>
      <li><strong>Supabase:</strong> Authentication and session management</li>
      <li><strong>Google Analytics (if enabled):</strong> Usage analytics</li>
    </ul>

    <h2>3. Legal Basis (GDPR)</h2>
    <ul>
      <li><strong>Strictly necessary:</strong> Legitimate interest (essential for service delivery)</li>
      <li><strong>Functional:</strong> Legitimate interest or consent, depending on jurisdiction</li>
      <li><strong>Analytics / marketing:</strong> Consent where required by law</li>
    </ul>

    <h2>4. How to Manage Cookies</h2>
    <p>You can control cookies through your browser settings. Most browsers allow you to:</p>
    <ul>
      <li>View and delete existing cookies</li>
      <li>Block all or certain cookies</li>
      <li>Block third-party cookies only</li>
    </ul>
    <p><strong>Note:</strong> Blocking strictly necessary cookies may prevent you from signing in or using core features.</p>

    <h2>5. Do Not Track</h2>
    <p>Some browsers send a &quot;Do Not Track&quot; (DNT) signal. We currently do not respond to DNT signals but respect your cookie preferences set in your browser.</p>

    <h2>6. Updates</h2>
    <p>We may update this Cookie Policy from time to time. The &quot;Last updated&quot; date at the top indicates when it was last revised. Continued use of the platform after changes constitutes acceptance.</p>

    <h2>7. More Information</h2>
    <p>
      For details on how we process your personal data, see our <Link to="/privacy-policy" className="text-primary underline hover:no-underline">Privacy Policy</Link>.
      <br />
      For questions: <a href="mailto:privacy@gcreators.me" className="text-primary underline hover:no-underline">privacy@gcreators.me</a>
    </p>
  </LegalLayout>
);

export default CookiePolicy;
