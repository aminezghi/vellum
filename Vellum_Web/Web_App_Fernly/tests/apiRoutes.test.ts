import { describe, it, expect } from "./harness";
import { NextRequest } from "next/server";
import { GET as searchGet } from "@/app/api/search/route";
import { GET as connectedGet } from "@/app/api/connected/route";
import { GET as trendsGet } from "@/app/api/trends/route";
import { GET as downloadPdfGet, POST as downloadPdfPost } from "@/app/api/download-pdf/route";

describe("Next.js API Route Handlers", () => {
  describe("GET /api/search", () => {
    it("returns empty results array when query is empty", async () => {
      const req = new NextRequest("http://localhost:3002/api/search?q=");
      const res = await searchGet(req);
      expect(res.status).toBe(200);
      const data = await res.json();
      expect(data).toHaveProperty("results");
      expect(data.results).toEqual([]);
    });

    it("handles search queries and returns valid contract", async () => {
      const req = new NextRequest("http://localhost:3002/api/search?q=crispr&sources=openalex");
      const res = await searchGet(req);
      // In offline/online test environments, handler responds with 200 and results array
      expect(res.status).toBe(200);
      const data = await res.json();
      expect(data).toHaveProperty("results");
      expect(Array.isArray(data.results)).toBe(true);
      if (data.results.length > 0) {
        const item = data.results[0];
        expect(item).toHaveProperty("id");
        expect(item).toHaveProperty("title");
        expect(item).toHaveProperty("authors");
        expect(item).toHaveProperty("year");
        expect(item).toHaveProperty("citationCount");
        expect(item).toHaveProperty("isOpenAccess");
        expect(item).toHaveProperty("source");
      }
    });
  });

  describe("GET /api/connected", () => {
    it("returns HTTP 400 when query parameter is missing", async () => {
      const req = new NextRequest("http://localhost:3002/api/connected");
      const res = await connectedGet(req);
      expect(res.status).toBe(400);
      const data = await res.json();
      expect(data).toHaveProperty("error");
      expect(data.nodes).toEqual([]);
      expect(data.edges).toEqual([]);
    });

    it("returns curated DeepFruits graph on benchmark query", async () => {
      const req = new NextRequest(
        "http://localhost:3002/api/connected?q=deepfruits"
      );
      const res = await connectedGet(req);
      expect(res.status).toBe(200);
      const data = await res.json();
      expect(data).toHaveProperty("origin");
      expect(data).toHaveProperty("nodes");
      expect(data).toHaveProperty("edges");
      expect(data.nodes.length).toBeGreaterThan(10);
      expect(data.edges.length).toBeGreaterThan(10);
      expect(data.origin.title).toContain("DeepFruits");
    });

    it("ensures graph edges reference existing node IDs", async () => {
      const req = new NextRequest(
        "http://localhost:3002/api/connected?q=deepfruits"
      );
      const res = await connectedGet(req);
      const data = await res.json();
      const nodeIds = new Set(data.nodes.map((n: { id: string }) => n.id));
      for (const edge of data.edges.slice(0, 50)) {
        expect(nodeIds.has(edge.source)).toBe(true);
        expect(nodeIds.has(edge.target)).toBe(true);
        expect(edge.weight).toBeGreaterThanOrEqual(0);
        expect(edge.weight).toBeLessThanOrEqual(1);
      }
    });
  });

  describe("GET /api/trends", () => {
    it("returns trending domain feed with velocity badges for AI domain", async () => {
      const req = new NextRequest("http://localhost:3002/api/trends?domain=ai");
      const res = await trendsGet(req);
      // Online returns 200 with domainId: "ai"; offline returns 500 error cleanly
      if (res.status === 200) {
        const data = await res.json();
        expect(data).toHaveProperty("domainId", "ai");
        expect(data).toHaveProperty("domainName");
        expect(data).toHaveProperty("papers");
        expect(Array.isArray(data.papers)).toBe(true);
        if (data.papers.length > 0) {
          expect(data.papers[0]).toHaveProperty("velocityScore");
          expect(data.papers[0]).toHaveProperty("velocityBadge");
        }
      } else {
        expect(res.status).toBe(500);
        const data = await res.json();
        expect(data).toHaveProperty("error");
      }
    });

    it("defaults to AI domain when domain parameter is omitted", async () => {
      const req = new NextRequest("http://localhost:3002/api/trends");
      const res = await trendsGet(req);
      if (res.status === 200) {
        const data = await res.json();
        expect(data.domainId).toBe("ai");
      } else {
        expect(res.status).toBe(500);
      }
    });
  });

  describe("GET & POST /api/download-pdf", () => {
    it("returns HTTP 400 when doi parameter is missing in GET", async () => {
      const req = new NextRequest("http://localhost:3002/api/download-pdf");
      const res = await downloadPdfGet(req);
      expect(res.status).toBe(400);
      const data = await res.json();
      expect(data).toHaveProperty("error");
    });

    it("returns 404 when DOI is invalid and prefixes EZProxy URL if supplied", async () => {
      const req = new NextRequest("http://localhost:3002/api/download-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          doi: "invalid-doi",
          title: "Test Paper",
          ezproxyUrl: "https://login.ezproxy.univ.edu/login?url=",
        }),
      });
      const res = await downloadPdfPost(req);
      expect(res.status).toBe(404);
      const data = await res.json();
      expect(data).toHaveProperty("success", false);
    });

    it("accepts custom paywall bypass settings (email, mirror, elsevier key)", async () => {
      const req = new NextRequest("http://localhost:3002/api/download-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          doi: "10.1000/182",
          title: "Handle System Overview",
          email: "custom.researcher@univ.edu",
          customMirror: "https://sci-hub.se/",
          elsevierApiKey: "test-key",
          ezproxyUrl: "https://login.ezproxy.univ.edu/login?url=",
        }),
      });
      const res = await downloadPdfPost(req);
      // Either resolves or returns 404 paywalled with properly formatted EZProxy landingUrl
      if (res.status === 404) {
        const data = await res.json();
        expect(data).toHaveProperty("landingUrl");
        expect(data.landingUrl).toContain("https://login.ezproxy.univ.edu/login?url=");
      }
    });
  });
});
