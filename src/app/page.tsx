"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to the companies page
    router.push("/companies");
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-semibold mb-2">Welcome to Pitch Platform</h1>
        <p className="text-muted-foreground">Redirecting to companies...</p>
      </div>
    </div>
  );
}
