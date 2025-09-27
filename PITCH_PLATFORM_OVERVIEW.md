# Pitch Platform Overview

## 🎯 Platform Purpose

The Pitch Platform is an AI-powered sales training and assessment tool where:
- **Sellers** practice pitching products/services to companies
- **Buyers** (company representatives) evaluate seller performance
- **AI Assistant** provides real-time coaching and guidance during pitches

## 📱 Key Pages

### 1. Companies List (`/companies`)
- Browse all available companies to pitch to
- See company size, industry, and job openings
- Filter by status (active, pending, contacted)
- Request new companies to be added

### 2. Company Details & Pitch Interface (`/company/[id]`)
**Left Side: AI-Powered Chat**
- Real-time pitch assistant powered by CopilotKit
- Helps sellers craft effective pitches
- Provides objection handling suggestions
- Guides through the sales process

**Right Side: Company Intelligence**
- Company overview and description
- Current needs and pain points
- Existing tech stack/solutions
- Key decision makers with focus areas
- Job openings and growth indicators

### 3. Seller's Pitch Score (`/pitch-score`)
- Comprehensive assessment tool for buyers
- Six evaluation criteria:
  - Product Knowledge (20% weight)
  - Communication (15% weight)
  - Needs Analysis (20% weight)
  - Solution Fit (20% weight)
  - Objection Handling (15% weight)
  - Professionalism (10% weight)
- Overall score calculation
- Recommendation system
- Export assessment reports

## 🔄 User Flow

### For Sellers:
1. Browse companies on `/companies`
2. Select a target company
3. Enter pitch interface at `/company/[id]`
4. Use AI assistant to prepare and deliver pitch
5. Receive feedback via pitch scores

### For Buyers:
1. Access company pitch sessions
2. Observe seller presentations
3. Navigate to `/pitch-score` after pitch
4. Complete detailed assessment
5. Submit evaluation for seller improvement

## 🤖 AI Integration

The platform leverages CopilotKit throughout:
- **Company Finder Assistant**: Helps sellers identify ideal prospects
- **Pitch Coach**: Real-time guidance during presentations
- **Assessment Helper**: Suggests constructive feedback based on scores

## 🛠️ Technical Stack

- **Frontend**: Next.js 15 with App Router
- **UI**: Tailwind CSS + shadcn/ui components
- **AI**: CopilotKit with LlamaIndex backend
- **State**: React hooks with CopilotKit's useCoAgent
- **Navigation**: File-based routing with dynamic segments

## 📊 Data Model

### Company
- Basic info (name, industry, size)
- Needs and challenges
- Current solutions
- Decision makers

### Pitch Session
- Seller information
- Company target
- Chat transcript
- Duration and engagement metrics

### Assessment
- Scored criteria
- Overall recommendation
- Detailed feedback
- Historical comparisons

## 🚀 Next Steps

1. **Authentication**: Add seller/buyer login system
2. **Database**: Connect to real company data
3. **Analytics**: Track pitch success rates
4. **Training Mode**: Practice pitches with AI buyers
5. **Leaderboards**: Gamify seller performance
