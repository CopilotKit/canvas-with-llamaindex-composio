# Routing Guide for Pitch Platform

## Overview

This is an AI-powered pitch platform where sellers practice and deliver pitches to companies (buyers) through an interactive chat interface. The platform uses **Next.js 15 with App Router** and integrates CopilotKit for AI assistance throughout the pitch process.

## File-Based Routing

### Basic Routes

Create routes by adding `page.tsx` files in the `src/app/` directory:

```
src/app/
├── page.tsx                    → / (redirects to /companies)
├── companies/
│   └── page.tsx               → /companies (list of companies)
├── company/
│   └── [id]/
│       └── page.tsx           → /company/[id] (pitch interface)
└── pitch-score/
    └── page.tsx               → /pitch-score (assessment tool)
```

### Dynamic Routes

For dynamic segments, use square brackets:
- `[id]` - Single dynamic segment: `/projects/123`
- `[...slug]` - Catch-all segments: `/blog/2024/01/post-title`
- `[[...slug]]` - Optional catch-all: `/docs` or `/docs/guide/routing`

## Creating New Pages

### 1. Basic Page Template

```tsx
"use client";

import { useCopilotAction } from "@copilotkit/react-core";
import { CopilotPopup } from "@copilotkit/react-ui";

export default function YourPage() {
  // Add CopilotKit actions
  useCopilotAction({
    name: "your_action",
    description: "Description of what this action does",
    parameters: [
      {
        name: "param",
        type: "string",
        description: "Parameter description",
        required: true,
      },
    ],
    handler: async ({ param }) => {
      // Your logic here
      return `Action completed with ${param}`;
    },
  });

  return (
    <div className="min-h-screen p-8">
      {/* Your page content */}
      
      {/* Optional: Add CopilotKit chat */}
      <CopilotPopup 
        instructions="Specific instructions for this page"
        labels={{
          title: "Page Assistant",
          initial: "How can I help?",
        }}
      />
    </div>
  );
}
```

### 2. Page with Navigation

To add navigation between pages, use Next.js `Link` component:

```tsx
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function PageWithNav() {
  return (
    <div>
      <Link href="/dashboard">
        <Button>Go to Dashboard</Button>
      </Link>
      
      {/* Programmatic navigation */}
      <Button onClick={() => window.location.href = '/settings'}>
        Settings
      </Button>
    </div>
  );
}
```

### 3. Dynamic Route Page

For pages with dynamic parameters:

```tsx
"use client";

import { use } from "react";

interface PageProps {
  params: Promise<{
    id: string;
  }>;
}

export default function DynamicPage({ params }: PageProps) {
  // In Next.js 15, params is a Promise
  const { id } = use(params);
  
  return <div>Item ID: {id}</div>;
}
```

## Navigation Components

### Using the Navigation Component

The project includes a navigation component. To use it, update your root layout:

```tsx
// src/app/layout.tsx
import { Navigation, MobileNavigation } from "@/components/navigation";

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <CopilotKit {...props}>
          <Navigation />
          <main className="pb-16 md:pb-0">
            {children}
          </main>
          <MobileNavigation />
        </CopilotKit>
      </body>
    </html>
  );
}
```

## CopilotKit Integration

### Available CopilotKit Features per Page

1. **CopilotPopup** - Floating chat interface
2. **CopilotChat** - Embedded chat component  
3. **useCopilotAction** - Define custom actions
4. **useCoAgent** - State synchronization (already used in main canvas)
5. **useCopilotChat** - Access chat functionality programmatically

### Example: Full-Featured Page

```tsx
"use client";

import { 
  useCopilotAction, 
  useCopilotChat,
  useCopilotReadable 
} from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";

export default function FeatureRichPage() {
  const [data, setData] = useState({ count: 0 });
  
  // Make data readable by AI
  useCopilotReadable({
    description: "Current page data",
    value: data,
  });
  
  // Define actions
  useCopilotAction({
    name: "increment_count",
    description: "Increment the counter",
    handler: () => {
      setData(prev => ({ count: prev.count + 1 }));
      return "Counter incremented";
    },
  });
  
  // Access chat programmatically
  const { appendMessage } = useCopilotChat();
  
  return (
    <div className="grid lg:grid-cols-[1fr_400px]">
      <div>
        {/* Page content */}
        <h1>Count: {data.count}</h1>
        <button onClick={() => appendMessage("Help me with this page")}>
          Ask for Help
        </button>
      </div>
      
      <CopilotChat 
        className="h-screen"
        instructions="Help the user interact with this page"
      />
    </div>
  );
}
```

## Best Practices

1. **Client Components**: Use `"use client"` directive for pages using CopilotKit hooks
2. **Loading States**: Add loading.tsx files for better UX during navigation
3. **Error Handling**: Create error.tsx files to handle page-level errors
4. **Metadata**: Export metadata for SEO in each page
5. **State Management**: Consider using the existing `useCoAgent` pattern for complex state

## Common Patterns

### Protected Routes

```tsx
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function ProtectedPage() {
  const router = useRouter();
  
  useEffect(() => {
    // Check authentication
    const isAuthenticated = checkAuth();
    if (!isAuthenticated) {
      router.push("/login");
    }
  }, [router]);
  
  return <div>Protected content</div>;
}
```

### Shared Layouts

Create layout.tsx in any directory to share UI:

```tsx
// src/app/dashboard/layout.tsx
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex">
      <aside className="w-64 p-4">
        {/* Sidebar */}
      </aside>
      <main className="flex-1">
        {children}
      </main>
    </div>
  );
}
```

## API Routes

For backend functionality, create route handlers:

```tsx
// src/app/api/custom/route.ts
import { NextResponse } from "next/server";

export async function GET(request: Request) {
  return NextResponse.json({ data: "value" });
}

export async function POST(request: Request) {
  const body = await request.json();
  return NextResponse.json({ received: body });
}
```

## Testing Your Routes

Run the development server and test:

```bash
npm run dev
```

Navigate to:
- http://localhost:3000/companies - Companies list (main landing)
- http://localhost:3000/company/1 - Company pitch interface
- http://localhost:3000/pitch-score?company=1 - Seller assessment tool

## Troubleshooting

1. **Page Not Found**: Ensure file is named `page.tsx` (not `index.tsx`)
2. **Hydration Errors**: Check for mismatched server/client rendering
3. **CopilotKit Not Working**: Verify page is wrapped in root layout's CopilotKit provider
4. **Dynamic Routes**: Remember to use `use()` hook for params in Next.js 15

## Next Steps

1. Add more pages following the patterns above
2. Implement proper data fetching (API routes or external APIs)
3. Add authentication/authorization as needed
4. Customize the navigation component for your needs
5. Integrate more CopilotKit features based on page requirements
