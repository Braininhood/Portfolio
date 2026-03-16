# Professional Portfolio

A comprehensive portfolio showcasing expertise across software development, data science, machine learning, cybersecurity, and full-stack web development. Each project demonstrates practical application of industry-standard technologies and methodologies.

---

## Table of Contents

- [Portfolio Overview](#portfolio-overview)
- [Project Categories](#project-categories)
- [Skills & Technologies](#skills--technologies)
- [Getting Started](#getting-started)
- [Contact](#contact)

---

## Portfolio Overview

This repository contains **22+ project categories** spanning:

| Domain | Highlights |
|--------|------------|
| **AI & Machine Learning** | NLP, computer vision, reinforcement learning, constraint satisfaction |
| **Data Science** | Regression, classification, ensemble methods, statistical modeling |
| **Web Development** | Django, Flask, React, full-stack microservices |
| **Cloud & APIs** | AWS Lambda, S3, RESTful APIs, serverless architecture |
| **Cybersecurity** | Threat detection, vulnerability scanning, encryption, GDPR compliance |
| **Data Automation** | Excel processing, cohort management, email automation |
| **Booking & Marketplace** | Multi-service booking (MultiBook), AI mentorship (Brain builders_lite) |
| **Systems Programming** | C algorithms, memory management, cryptography |

---

## Project Categories

### [AI & Machine Learning](./AI-Projects/)

AI and machine learning projects demonstrating NLP, computer vision, genetic algorithms, and reinforcement learning.

| Project | Description |
|---------|-------------|
| **attention/** | BERT-based attention mechanism for masked language modeling (`mask.py`) |
| **crossword/** | Constraint satisfaction system for crossword puzzle generation |
| **degrees/** | Six Degrees of Kevin Bacon using breadth-first search |
| **heredity/** | Bayesian network for genetic inheritance modeling |
| **knights/** | Propositional logic solver for logic puzzles |
| **minesweeper/** | Logical inference AI agent for Minesweeper |
| **nim/** | Reinforcement learning (Q-learning) for Nim game |
| **pagerank/** | PageRank algorithm for web page ranking (corpus of HTML files) |
| **parser/** | Context-free grammar NLP sentence parser |
| **shopping/** | ML model for shopping behavior prediction |
| **tictactoe/** | Minimax algorithm for adversarial game AI |
| **traffic/** | TensorFlow CNN for traffic sign recognition |

---

### [Data Science](./Data-Science/)

Statistical modeling, exploratory analysis, and machine learning with real-world datasets. Organized in **DS0–DS9** folders.

| Folder | Focus |
|--------|-------|
| **DS0** | Polynomial regression, advertising data, get_dummies, model selection |
| **DS2** | Population noise modeling |
| **DS3** | Boston housing price prediction (Ridge, Lasso) |
| **DS4** | Polynomial regularization |
| **DS5** | Bacteria classification |
| **DS6** | Heart disease classification (KNN, logistic regression) |
| **DS7** | Insurance claim prediction |
| **DS8** | Land type classification |
| **DS9** | Heart disease prediction model comparison |

**Techniques:** Linear/polynomial regression, Ridge/Lasso regularization, KNN, logistic regression, feature engineering, one-hot encoding, model evaluation

---

### [Machine Learning & Data Science](./ML-AI(Data-Science)/)

Advanced ML algorithms: decision trees, ensemble methods, and hyperparameter optimization.

| Project | Focus |
|---------|-------|
| **ML_AI_1** | Decision tree classification (election prediction) |
| **ML_AI_2** | Decision tree visualization |
| **ML_AI_3** | Decision trees from scratch |
| **ML_AI_4** | Overfitting and bagging |
| **ML_AI_5** | Bagging classification |
| **ML_AI_6** | Tree correlation analysis |
| **ML_AI_7** | Feature importance analysis |
| **ML_AI_8** | Hyperparameter tuning (grid/random search) |
| **ML_AI_9** | Boosting regressors (Gradient Boosting, AdaBoost) |

---

### [Data Analysis](./Data-Analysis/)

Data manipulation, visualization, and statistical analysis with Python. **25+ Jupyter notebooks** plus project folder.

**Data-Analysis_project/** — Payment transaction analysis: Visa/MasterCard distribution, temporal trends, geographical patterns, ZIP code analysis, correlation studies

**Notebooks (root):** `numpy.ipynb`, `Wrangle_the_data.ipynb`, `Working_with_Strings.ipynb`, `Sorting_and_cleaning.ipynb`, `Filtering_data_with_Pandas.ipynb`, `Describing_and_Interrogating_Data.ipynb`, `Data_cleaning_with_normalisation_challenges.ipynb`, `Data_retrieval.ipynb`, `Encoding_and_Dummy_Coding.ipynb`, `Numpy_mini_project.ipynb`, `Visualisation_with_matplotlib.ipynb`, `Visualisation_with_Seaborn.ipynb`, `Testing_for_normal_distributions.ipynb`, `Probability.ipynb`, `Correlation.ipynb`, `Correlation_with_linregress.ipynb`, `Air_quality_mini_project.ipynb`, `ADVANCED_Bus_Data_Emissions_Pandas_Analysis.ipynb`, `Movies Mini-project.ipynb`, `NBA.ipynb`, `Page_Views_Project.ipynb`, `Sea-Level predictor project.ipynb`, `Sea_Level_Project.ipynb`, `Data investigation task.ipynb`, `Data_Exploration_project.ipynb`, `Decision_Tree_coded_mode.ipynb`, `SQL databases worksheet.ipynb`, `R worksheet.ipynb`, `Dictionaries Steam Challenge.ipynb`, `Fundamentals_Extension_Challenge.ipynb`

---

### [Data Automation](./Data-Automation/)

Full-stack web application for Excel processing, cohort management, and email automation.

**Backend (Django):** `data_automation/`, `data_processing/`, `email_system/`, `api/` — REST API, Celery tasks, Pandas/OpenPyXL processing  
**Frontend (React):** `frontend/` — Dashboard, FileUpload, MicrosoftFormsImport, CohortManagement, EmailSystem, BPADemo, Reports, DataAnalysis

**Features:** Dual file upload (Excel + Microsoft Forms), 11 cohort types, Gmail integration with HTML emails and embedded charts, BPA for duplicate resolution, real-time dashboard, Celery + Redis

**Stack:** Django 4.2, Django REST Framework, React 18, Tailwind CSS, Pandas, OpenPyXL, Matplotlib, Seaborn

---

### [Django Web Applications](./Django/)

Full-stack web applications built with Django and modern frontend technologies.

| Project | Description |
|---------|-------------|
| **fullstack_developer_capstone/** | Dealership management system: React frontend, Django API gateway, Node.js/MongoDB microservices, Flask sentiment analysis (NLTK), Docker Compose. 50+ dealers, 6 car makes, 21 models, real-time sentiment on reviews |
| **data_project/** | Data Visualization: Upload CSV/Excel/SQLite, connect MySQL/PostgreSQL/SQL Server/Supabase, data cleaning (outliers, normalization), Matplotlib/Seaborn charts (bar, line, scatter, heatmap, bubble), encrypted credentials, GDPR compliance |
| **wiki/** | Wikipedia-like encyclopedia with Markdown support |
| **mail/** | Single-page email client with REST API (inbox, sent, archive, drafts) |
| **commerce/** | E-commerce auction site with bidding, watchlist, categories |
| **network/** | Twitter-like social network with posts, follow/unfollow, likes, pagination |

**Technologies:** Django MVT, React 18, Node.js/Express, MongoDB, Docker Compose, Material-UI, Bootstrap, SQLAlchemy, Cryptography

---

### [MultiBook](./MultiBook/) — Multi-Service Booking System

**Status: Production-ready** | Django REST + Next.js | PostgreSQL (Supabase) | AWS

Enterprise-grade appointment booking system (HouseCallPro + Bookly style) for cleaning, maintenance, landscaping, handyman, property boards, housing associations.

**Features:** Multi-step booking (8 steps), multi-service orders, guest checkout, subscriptions (weekly/biweekly/monthly), staff & service management, postcode-first service areas, role-based dashboards (Admin, Manager, Staff, Customer), coupon system, Google/Outlook/Apple Calendar sync, 35 database tables, 80 CHECK constraints, AWS deployment

**Structure:** `backend/` (Django REST API — accounts, services, staff, customers, appointments, orders, subscriptions, coupons, calendar_sync, payments, notifications, reports), `frontend/` (Next.js), `docs/` (AWS deployment, database, calendar setup)

---

### [Brain builders_lite](./Brain%20builders_lite/) — AI-Powered Mentorship Platform

**Status: Production** | React 18 + TypeScript + Vite | Supabase | Stripe Connect

Full-stack mentorship marketplace where experts offer consultations, digital products, and AI-powered guidance. [Live Demo](https://gcreators.me)

**Features:** Mentor discovery with AI recommendations, consultation booking (Google/Outlook calendar), digital product sales, real-time messaging, AI avatars (knowledge-base-powered assistants), Stripe Connect for payouts, admin panel, video responses, multi-language (DeepL/Google Translate), voice AI (ElevenLabs, Google TTS)

**Stack:** React 18, TypeScript, Vite, Tailwind CSS, Radix UI, Supabase (PostgreSQL, Auth, Storage, Realtime, Edge Functions), Stripe, OpenAI/Gemini/Claude, Playwright (E2E)

---

### [Flask Web Applications](./Flask/)

**jmgdo-microservices/** — Flask microservices and API patterns:

| Subfolder | Description |
|-----------|-------------|
| **CRUD/** | RESTful product management API (products.py) |
| **swagger_example/** | OpenAPI/Swagger documentation with interactive testing |
| **graphql_example/** | Node.js GraphQL server for US cities data, Docker support |

**Technologies:** Flask, Flask-RESTx, Swagger/OpenAPI, GraphQL, Docker

---

### [AWS & API Development](./AWS_Data_API/)

Cloud services and API development with AWS.

**Notebooks:** `AssessingAPIData.ipynb`, `IPAddressValidationAndGeolocation.ipynb`, `Lambda_funct.ipynb`, `Lambda_S3.ipynb`, `Reading_from_and_saving_to_S3.ipynb`

**AWS_Data_API_project/** — Full project with documentation: `Python-Project.ipynb`, `Project-backend-only.ipynb`, `List of information about project.docx`, `Test from Postman.docx`, `Test in AWS.docx`, `Test plan.docx`, `Vulnerabilities and cybersecurity concerns.docx`

**Technologies:** AWS Lambda, S3, API Gateway, boto3, python-dotenv

---

### [Cybersecurity & Tech Support](./Cybersecurity%20%26%20TechSupport/)

Security tools, monitoring, and compliance applications.

| Project | Description |
|---------|-------------|
| **SecurityNetworkMonitor/** | AI-powered monitoring (Django/React), ML threat detection (RandomForest), WebSocket dashboard, Celery, Redis |
| **GDPR_Compliance_Checker/** | PyQt5 GUI: cookie consent, privacy policy, data subject rights, third-party detection, remediation reports |
| **Website-Vulnerability-Scanner/** | OWASP checks, port scanning (TCP/UDP), CMS detection, SQLi/XSS, API discovery, Tkinter GUI |
| **System-Monitor/** | Real-time CPU, memory, disk, process, network monitoring (psutil) |
| **System-Information-Collector/** | Cross-platform system info (Windows/Linux): OS, hardware, network, software, browsers, antivirus |
| **Network-Monitoring-Tool/** | Scapy-based port scan and SYN flood detection, CustomTkinter GUI |
| **Hardware-checker/** | Hardware detection, stress testing, professional monitor GUI, WMI repair tools |
| **OTP-Generator/** | Fibonacci-based OTP with proportional mean, Tkinter GUI |
| **Fibonacci-numbers/** | Fibonacci cipher and OTP notebooks |
| **CIPHER-APPLICATION/** | Web-based cipher (Caesar, Vigenère, Atbash, Fibonacci), Flask, SQLite |
| **Checker-connection-DNS-mapping/** | Server connection monitoring, DNS mapping (A, AAAA, MX, NS, CNAME, TXT) |
| **Secure-File-Storage-Blockchain/** | AES-256 + blockchain for file integrity, Web/CLI/Desktop (PyQt5) |
| **PasswordManager/** | Zero-knowledge password manager: DesktopApp (PyQt5), WebApp (Django + React) |

---

### [Python Programming](./Python_practice/)

**Standalone projects (30+):** `adieu`, `bank`, `bitcoin`, `camel`, `coke`, `deep`, `dna`, `einstein`, `emojize`, `extensions`, `faces`, `fiftyville`, `figlet`, `fuel`, `game`, `grocery`, `indoor`, `interpreter`, `lines`, `meal`, `nutrition`, `outdated`, `pizza`, `plates`, `playback`, `professor`, `response`, `scourgify`, `shirt`, `shirtificate`, `taqueria`, `tip`, `twttr`, `watch`

**IBM Practice/** — `lab Flask/` (sentiment_analysis, project_emotion, lab-site), `PY0101EN` series, `Pandas_Practice.ipynb`, `Simple_API_2__v2.ipynb`, web scraping labs

**Root notebooks:** `Lesson*Practice*.ipynb`, `Exercise*Challenges.ipynb`, `FileHandlingChallenge.ipynb`, `Fun_calc.ipynb`, `WorkWithArraysChallenges.ipynb`, `LoopsChallanges.ipynb`, `DealingWithErrors.ipynb`

---

### [SQL Database Projects](./SQL_practice/)

| Project | Description |
|---------|-------------|
| **songs/** | SQLite: `1.sql`–`8.sql`, `answers.txt` — SELECT, ORDER BY, aggregates, grouping |
| **movies/** | SQLite: `1.sql`–`13.sql` — joins, subqueries, date/time, complex analytics |

---

### [Web Development](./HTML_JS_CSS/)

| Project | Description |
|---------|-------------|
| **search/** | Google-like interface (main, image, advanced), `server.py` for testing |
| **trivia/** | Interactive quiz (multiple choice, free response) |
| **homepage/** | Multi-page portfolio (index, skills, experience, contact) |
| **IBM exercises/** | See below |

**IBM exercises/** — Full collection:

- **React.js/** — `MyFirstApp`, `ToDoList`, `EventPlanner`, `Feedback_Form`, `Content_rating`, `Custom_hook`, `Ecommers_rtk`, `e-plantShopping`, `conference_event_planner`
- **Node.js/** — `expressBookReviews` (Express book review API)
- **JS/** — `Add_Delete task`, `Converter`, `SinglePageWebsite`
- **Ex1/**, **Ex2/** — Additional exercises
- **Simple-Interest-Calculator-master/** — Interest calculator
- **solarsystem.html**, **Easy convert.html** — Standalone HTML/CSS/JS

---

### [C Language Projects](./C%20Language/)

| Category | Projects |
|----------|----------|
| **Console** | `hello`, `cash`, `credit`, `mario1`, `mario2`, `readability`, `scrabble` |
| **Cryptography** | `caesar`, `substitution` |
| **Memory** | `filter-less`, `filter-more`, `recover`, `speller`, `volume` |
| **Algorithms** | `plurality`, `runoff`, `tideman` |
| **Data Structures** | `inheritance`, `sort`, `world` |

---

### [Software Testing](./Testing/)

**pytest projects:** `test_twttr`, `test_plates`, `test_fuel`, `numb3rs`, `test_bank`, `jar`, `um`, `working`, `seasons`

**Tutorials:** `TestingSoftware.ipynb`, `TestingSoftwareAutomation.ipynb`, `TestingAutomation2.ipynb` — TDD, CI/CD, performance, security testing

---

## Skills & Technologies

### Programming Languages
Python · JavaScript · TypeScript · SQL · C · HTML/CSS · R

### Frameworks & Libraries
Django · Flask · React 18 · Next.js · Express.js · Redux Toolkit · Material-UI · Bootstrap · Tailwind CSS · Vite

### Data & ML
Pandas · NumPy · Scikit-learn · TensorFlow · NLTK · Matplotlib · Seaborn · Recharts

### Cloud & DevOps
AWS (Lambda, S3, API Gateway, EC2) · Docker · Docker Compose · Celery · Redis · Stripe Connect

### Databases
PostgreSQL · MySQL · SQLite · MongoDB · Supabase · SQLAlchemy

### Security & Testing
Cryptography · Scapy · psutil · pytest · OWASP · GDPR compliance · PyQt5 · CustomTkinter

---

## Getting Started

Each project includes its own `README.md` (where available) with setup instructions.

**Typical setup:**
```bash
# Python projects
pip install -r requirements.txt
python manage.py migrate  # Django/Flask
python manage.py runserver

# Node/React projects
npm install
npm start
```

---

## Contact

| Channel | Link |
|---------|------|
| **Email** | [braininhood@gmail.com](mailto:braininhood@gmail.com) |
| **LinkedIn** | [linkedin.com/in/andrii-b-191a072ba](https://www.linkedin.com/in/andrii-b-191a072ba) |

---

*This portfolio is continuously updated with new projects as skills expand. Thank you for visiting.*
