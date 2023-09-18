presentation_prompt = """Write a presentation/powerpoint about the user's topic. You only answer with the presentation. Follow the structure of the example.
Notice
-You do all the presentation text for the user.
-You write the texts no longer than 250 characters!
-You make very short titles!
-You make the presentation easy to understand.
-The presentation has a title slide first
-The presentation has a table of contents.
-The presentation has a summary.
-At least 8 slides.

Example! - Stick to this formatting exactly!
#Title: TITLE OF THE PRESENTATION

#Slide: 1
#Header: table of contents
#Content: 1. CONTENT OF THIS POWERPOINT
2. CONTENTS OF THIS POWERPOINT
3. CONTENT OF THIS POWERPOINT
...

#Slide: 2
#Header: TITLE OF SLIDE
#Content: CONTENT OF THE SLIDE

#Slide: 3
#Header: TITLE OF SLIDE
#Content: CONTENT OF THE SLIDE

#Slide: 4
#Header: TITLE OF SLIDE
#Content: CONTENT OF THE SLIDE

#Slide: 5
#Headers: summary
#Content: CONTENT OF THE SUMMARY

#Slide: END"""

personalized_pitch_deck_prompt = """
Write a presentation/powerpoint about this company based on its description delimited by <d> tags:
Description: 
<d>
{topic}
<d>

Make the presenation personalized to {recipient_name}. Address them by name on the first slide with some sort of greeting. Also try to draw connections between their firm's investments, thesis, etc and our company.
Here is some information about them delimited by <l> tags:
<l>
The Investor and Firm Details details are:
- Name: {recipient_name}
- Entity / Firm: {entity_name}
{entity_info}
- Recent Tweets: {recent_tweets}
<l>
You only answer with the presentation. Follow the structure of the example.
Notice
-You do all the presentation text for the user.
-You write the texts no longer than 250 characters!
-You make very short titles!
-A slide complementing them on one of their recent tweets if they are available in the info
-You make the presentation easy to understand.
-The presentation has a table of contents.
-The presentation has a summary.
-At least 8 slides.

Example! - Stick to this formatting exactly!
#Title: TITLE OF THE PRESENTATION

#Slide: 1
#Header: table of contents
#Content: 1. CONTENT OF THIS POWERPOINT
2. CONTENTS OF THIS POWERPOINT
3. CONTENT OF THIS POWERPOINT
...

#Slide: 2
#Header: GREETINGS!
#Content: GREET {recipient_name} with a personalized message

#Slide: 3
#Header: TITLE OF SLIDE
#Content: CONTENT OF THE SLIDE

#Slide: 4
#Header: TITLE OF SLIDE
#Content: CONTENT OF THE SLIDE

#Slide: 5
#Header: TITLE OF SLIDE
#Content: CONTENT OF THE SLIDE

#Slide: 6
#Headers: summary
#Content: CONTENT OF THE SUMMARY

#Slide: END
"""




pitch_content = """
TAGLINE:::
We empower developers to build secure, decentralized AI tailored to individual needs. Customize your AI symphony.

THE PROBLEM:::
1. AI Agents are isolated from collaboration with each other, existing business services, and average consumers
2. Fragmentation Hinders AI Adoption: Unity, Efficiency, Compatibility, Entry, & Security
3. Lack of Unity: Disjointed, over-technical user experiences.
- Operational Inefficiency: Reduced productivity.
- Limited Cross-Compatibility: Missed synergistic possibilities.
- Barrier to Entry: Discourages widespread adoption.
- Security Concerns: Inconsistent security protocols.

ELYSIUM'S SOLUTION:::
1. Seamless User Experience
- Customize agent personalities and settings for a tailored AI experience.
2. Dynamic Ecosystem Integration
- Integrate multiple AI agents for efficient task management.
3. Unified AI Network
- Sync effortlessly with existing business systems for smooth transitions.
4. Secure and Trustworthy Platform
- Elysium uses a blend of decentralized and conventional security protocols for robust data protection
With Elysium OS, we provide a unified, easy-to-navigate portal for accessing your personalized AI Butler or Chief of Staff. 

OUR OFFERINGS:::
1. Elysium OS - web and hologram on PC and Mac
AI Personal Butler or Enterprise Chief of Staff (COS)

Elysium OS provides 24/7 access to your personal Butler—or Chief of Staff for our enterprise customers—across various platforms such as text, voice, and web chat. It serves as the unified portal for managing your AI agents, offers seamless interaction, robust customization, and powerful capabilities

2. Automation Station
The Central Hub for Sourcing and Deploying AI Agents

Automation Station streamlines AI Agent recruitment and deployment. Our dynamic marketplace enables task assignment, seamless collaboration, and easy business integration. We manage agent payments, eliminating API key hassles. Experience automation, simplified.

TARGET CUSTOMER:::
Developers:

1. Shared Problem We Solve
AI Agents have technical setups are not accessible from a single platform, and lack connectivity to other agents and exiting business services

2. Elysium as a Value-Added Catalyst
Providing single intuitive entry point for consumers to use their technology via Elysium OS (AI Butler / Chief of Staff)
Platforming all their AI Agents in one place where transactions between agents or between agents and existing businesses will occur via AutomationStation (Agent recruiting and deployment marketplace)

CAPITAL RAISE:::
We are raising
$3,500,000 in our Seed round
The purpose of the fundraising:
1. Significant hirings: UX/UI Designers, OS Lead, Backend & Support Devs
2. Growth via new marketing channels, ready resource for enterprise fulfillment, and scaling audits
3. Development: Full build of our platform/ public launch

Our Team:::
Our experienced team of AI experts and industry veterans is dedicated to achieving our mission.

Michael Gruen
Chief Executive Officer

Doug Schaer
Chief Business Officer

Peter Krenesky
CTO

Arben Gutierrez-B.
Head of Product

Michael Daigler
VP of Engineering

Oversight Committee:::
Yohei Nakajima
AI Solutions Architectural Consultant, Scholar-in-Residence

Brock Pierce
Chief Evangelist

Elysium's Advisors:::
World-Class Advisors whose expertise and experience are sure to guide Elysium to Success

Marc Randolph
Co-founder and first CEO of Netflix (NFLX:NASDAQ), Marc is a seasoned Silicon Valley entrepreneur and investor. His portfolio includes Looker Data Sciences, Chubbies Shorts, and MentorBox, etc.

G. Scott Paterson
Director of Lionsgate Entertainment Canada Corp (LGF.A:NYSE), Scott is an accomplished investment banker with 30+ years of experience in tech and media sectors. He has served as CEO / Board of Yorkton Securities, NeuLion, QYOU (TSX.V: QYOU), and more.

Anthony Scaramucci
Former White House Director of Communications and founder of SkyBridge Capital, Anthony is a well-known financier and political commentator. His extensive career highlights include stints at Goldman Sachs and Lehman Brothers.

Jay Abraham
Mentor of Mentors, Jay is the founder and CEO of The Abraham Group, and has advised over 10,000 clients across 400+ industries, generating billions in revenue. Innovator behind "Three Ways to Grow a Business" model, Jay is a sought-after author, speaker, and mentor in the field of business growth and marketing.

Ory Rinat
Former Chief Digital Officer at The White House and Founder & CEO of Urban Legend. Ory has been at the forefront of digital strategies and political campaigns. A Columbia and Georgetown Law alumnus, Ory's innovation now drives his influencer marketing tech venture in D.C.

Dr. Jeffrey Pfeffer
Professor at Stanford’s Graduate School of Business, Jeffrey is a revered figure in organizational behavior. As a thought leader in business theories he has written 16 influential books, is involved in Business 2.0 and Fortune.com, and has served on the boards of Quantum Leap Healthcare, SonoSite, etc.
"""