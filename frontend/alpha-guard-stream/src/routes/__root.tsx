import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  Link,
  createRootRouteWithContext,
  useRouter,
  HeadContent,
  Scripts,
} from "@tanstack/react-router";
import { useEffect, type ReactNode } from "react";

import appCss from "../styles.css?url";
import { reportLovableError } from "../lib/lovable-error-reporting";

function NotFoundComponent() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <div className="mono label-xs">404 · route not found</div>
        <h1 className="mt-2 mono text-6xl font-bold text-foreground">404</h1>
        <p className="mt-3 text-sm text-muted-fg">
          No handler registered for this path.
        </p>
        <div className="mt-6">
          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-sm bg-accent-cyan px-3 py-1.5 mono text-[12px] font-medium text-background hover:opacity-90"
          >
            return to terminal
          </Link>
        </div>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  console.error(error);
  const router = useRouter();
  useEffect(() => {
    reportLovableError(error, { boundary: "tanstack_root_error_component" });
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <div className="mono label-xs text-danger">runtime exception</div>
        <h1 className="mt-2 text-xl font-semibold tracking-tight text-foreground">
          Terminal encountered an error
        </h1>
        <p className="mt-2 mono text-[12px] text-muted-fg break-all">
          {error.message}
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <button
            onClick={() => {
              router.invalidate();
              reset();
            }}
            className="inline-flex items-center justify-center rounded-sm bg-accent-cyan px-3 py-1.5 mono text-[12px] font-medium text-background hover:opacity-90"
          >
            retry
          </button>
          <a
            href="/"
            className="inline-flex items-center justify-center rounded-sm border border-border bg-panel px-3 py-1.5 mono text-[12px] font-medium text-foreground hover:bg-panel-elevated"
          >
            home
          </a>
        </div>
      </div>
    </div>
  );
}

const TITLE = "QuantStream Labs · Market-Data Reliability Terminal";
const DESC =
  "Detect fake alpha caused by corrupted market data. Deterministic replay, checksum-verified validation, and raw-vs-cleaned strategy divergence.";

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: TITLE },
      { name: "description", content: DESC },
      { property: "og:title", content: TITLE },
      { property: "og:description", content: DESC },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
    links: [
      { rel: "stylesheet", href: appCss },
      { rel: "icon", href: "/favicon.ico", type: "image/x-icon" },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <HeadContent />
      </head>
      <body className="bg-background text-foreground">
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();
  return (
    <QueryClientProvider client={queryClient}>
      <Outlet />
    </QueryClientProvider>
  );
}
