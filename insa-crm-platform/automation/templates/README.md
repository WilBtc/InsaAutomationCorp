# Mautic Email Templates for INSA Automation
**Created:** October 18, 2025
**Purpose:** Professional email templates for marketing automation campaigns

---

## 📧 Template Library (5 Templates)

### 1. Welcome Email (`1-welcome-email.html`)
**Purpose:** First contact with new subscribers
**Trigger:** Form submission, list subscription
**Sends:** Immediately after subscription

**Content:**
- Warm welcome message
- Overview of INSA services
- What to expect (next steps)
- Recommended resources
- Call-to-action: Get Started

**Variables:**
- `{contactfield=firstname}` - Recipient's first name

---

### 2. IEC 62443 Nurture Series (`2-nurture-iec62443-series.html`)
**Purpose:** Educational email series (5-part)
**Trigger:** Lead qualification, interest in compliance
**Sends:** Weekly over 5 weeks

**Series Content:**
- Email 1: Introduction to IEC 62443
- Email 2: Risk Assessment & Vulnerability Scanning
- Email 3: Network Segmentation & Purdue Model
- Email 4: Access Control & Authentication
- Email 5: Continuous Monitoring & Compliance

**Variables:**
- `{contactfield=firstname}` - Recipient's first name
- `{email_number}` - Part number (1-5)

**CTA:** Free assessment, download resources

---

### 3. Event Invitation (`3-event-invitation.html`)
**Purpose:** Webinar/workshop registration
**Trigger:** Segment targeting, campaign launch
**Sends:** 2-3 weeks before event

**Content:**
- Event details (date, time, location)
- Agenda and speakers
- What attendees will learn
- Registration CTA
- Calendar integration
- Exclusive bonuses

**Variables:**
- `{contactfield=firstname}`
- `{event_name}` - Event title
- `{event_tagline}` - Event subtitle
- `{event_date}` - Date (e.g., "November 15, 2025")
- `{event_time}` - Time (e.g., "9:00 AM - 12:00 PM EST")
- `{event_duration}` - Duration (e.g., "3 hours")
- `{event_location}` - Venue (e.g., "Virtual" or address)
- `{event_address}` - Full address (if physical)
- `{event_registration_url}` - Registration link
- `{seats_remaining}` - Available spots
- `{event_calendar_url}` - Calendar file
- `{event_waitlist_url}` - Waitlist link

---

### 4. Monthly Newsletter (`4-newsletter-monthly.html`)
**Purpose:** Regular communication with subscribers
**Trigger:** Scheduled (monthly)
**Sends:** First Thursday of each month

**Content:**
- This month in numbers (stats)
- Featured articles (3-4)
- Upcoming events
- Recommended resources
- Pro tip of the month
- Customer spotlight

**Variables:**
- `{contactfield=firstname}`
- `{month}` - Month name (e.g., "October")
- `{year}` - Year (e.g., "2025")
- `{webinar_date}` - Upcoming webinar date
- `{webinar_time}` - Webinar time
- `{webinar_registration_url}` - Registration link

**Content Blocks:** Update monthly with fresh articles and stats

---

### 5. Customer Onboarding (`5-customer-onboarding.html`)
**Purpose:** New customer welcome & setup guide
**Trigger:** Opportunity won, first purchase
**Sends:** Within 24 hours of customer conversion

**Content:**
- Welcome message
- 30-day success plan
- Week 1 checklist (5 tasks)
- Essential resources
- Success team introduction
- Exclusive benefits
- What's next

**Variables:**
- `{contactfield=firstname}`
- `{account_manager_name}` - Success manager name
- `{account_manager_email}` - Manager email
- `{account_manager_phone}` - Manager phone
- `{account_manager_calendar}` - Booking link

**CTA:** Access portal, schedule kickoff call

---

## 🎨 Design System

### Brand Colors
```css
--insa-primary: #003366    /* Dark Blue - Headers, primary brand */
--insa-secondary: #0066CC  /* Blue - Links, secondary elements */
--insa-accent: #FF6600     /* Orange - CTAs, highlights */
--insa-light: #F5F5F5      /* Light Gray - Background */
--insa-text: #333333       /* Dark Gray - Body text */
```

### Typography
- **Font Family:** 'Helvetica Neue', Helvetica, Arial, sans-serif
- **Body Text:** 16px, line-height 1.6
- **H1:** 24-28px, color: #003366
- **H2:** 20px, color: #0066CC

### Components
- **Button Primary:** Orange (#FF6600), 15px padding, border-radius 5px
- **Button Secondary:** Blue (#0066CC)
- **Cards:** Light gray background (#f9f9f9), 5px radius
- **Highlights:** Left border 4px solid color, 20px padding

---

## 📱 Responsive Design

All templates are mobile-responsive with breakpoints at 600px.

**Mobile Optimizations:**
- Reduced padding (40px → 20px)
- Smaller headings (24px → 20px)
- Stacked layouts for grids
- Full-width buttons
- Larger tap targets

---

## 🔧 How to Use in Mautic

### Step 1: Upload Template
1. Login to Mautic: http://100.100.101.1:9700
2. Go to **Channels** → **Emails**
3. Click **New**
4. Select **Code Mode**
5. Paste HTML template
6. Save as template

### Step 2: Customize Content
Replace placeholder variables with Mautic tokens:
- `{contactfield=firstname}` - Auto-populated from contact
- `{event_name}` - Enter your event name
- `{unsubscribe_url}` - Mautic auto-generates
- `{webview_url}` - Mautic auto-generates

### Step 3: Test Email
1. Click **Send Example**
2. Enter test email address
3. Verify rendering on desktop + mobile
4. Test all links and CTAs

### Step 4: Create Campaign
1. Go to **Campaigns**
2. Create new campaign
3. Add email to workflow
4. Set trigger conditions
5. Activate campaign

---

## 📊 Email Performance Benchmarks

### Industry Standards (B2B Industrial)
- **Open Rate:** 20-25%
- **Click-Through Rate:** 3-5%
- **Unsubscribe Rate:** <0.5%
- **Bounce Rate:** <2%

### INSA Targets (Year 1)
- **Open Rate:** >25%
- **Click-Through Rate:** >5%
- **Lead Generation:** 100 MQLs/month
- **Conversion Rate:** 10% (MQL to SQL)

---

## 🧪 A/B Testing Ideas

### Subject Lines
- **A:** "Welcome to INSA Automation!" (direct)
- **B:** "Your Industrial Security Journey Starts Here" (benefit-focused)

### CTAs
- **A:** "Get Started →" (generic)
- **B:** "Access Your Free Assessment →" (specific value)

### Send Times
- **A:** Tuesday 10 AM
- **B:** Thursday 2 PM

---

## 🚀 Quick Start

**Deploy All Templates in 30 Minutes:**

1. **Login to Mautic:** http://100.100.101.1:9700 (admin/mautic_admin_2025)
2. **Create Email 1 (Welcome):**
   - Channels → Emails → New
   - Name: "Welcome Email"
   - Subject: "Welcome to INSA Automation, {contactfield=firstname}!"
   - Paste HTML from `1-welcome-email.html`
   - Save

3. **Create Email 2-5:** Repeat for each template

4. **Test All Templates:**
   - Send test emails
   - Verify mobile rendering
   - Check all links

5. **Create First Campaign:**
   - Campaigns → New
   - Add "Welcome Email" to workflow
   - Trigger: Contact subscribes
   - Activate

**Total Time:** ~30 minutes for all 5 templates

---

## 📞 Support

**Questions?**
- Email: w.aroca@insaing.com
- Mautic Docs: ~/MAUTIC_MCP_COMPLETE_GUIDE.md
- Template Issues: Open GitHub issue

---

**Created By:** Claude Code (Anthropic)
**Last Updated:** October 18, 2025
**Version:** 1.0
