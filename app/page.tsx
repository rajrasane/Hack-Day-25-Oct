"use client";

import { FormEvent, useState } from "react";
import { MigrationRequest, sendMigrationSignal, startMigration } from "./lib/migration-client";

type Phase = "idle" | "parsing" | "analyzing" | "review";
type Decision = "APPROVE" | "REJECT" | null;

const originalManifest = `Django==4.2.7
celery==5.3.4
redis==5.0.1
cryptography==41.0.5
requests==2.31.0
psycopg2-binary==2.9.9`;

const upgradedManifest = `Django==5.0.6
celery==5.4.0
redis==5.0.4
cryptography==42.0.8
requests==2.32.3
psycopg2-binary==2.9.9`;

const sampleRequest: MigrationRequest = {
  repo_url: "https://github.com/acme/atlas-api",
  config_path: "requirements.txt",
  project_type: "Python"
};

function Icon({ name, size = 16 }: { name: "arrow" | "check" | "chevron" | "shield" | "alert" | "close" | "spark"; size?: number }) {
  const common = { width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  if (name === "arrow") return <svg {...common}><path d="M5 12h13M13 6l6 6-6 6" /></svg>;
  if (name === "check") return <svg {...common}><path d="m5 12 4 4L19 6" /></svg>;
  if (name === "chevron") return <svg {...common}><path d="m7 9 5 5 5-5" /></svg>;
  if (name === "shield") return <svg {...common}><path d="M12 3 20 6v5c0 5.1-3.4 8.7-8 10-4.6-1.3-8-4.9-8-10V6l8-3Z" /><path d="m8.5 12 2.2 2.2 4.8-4.8" /></svg>;
  if (name === "alert") return <svg {...common}><path d="M12 3 22 20H2L12 3Z" /><path d="M12 9v4M12 17h.01" /></svg>;
  if (name === "close") return <svg {...common}><path d="m7 7 10 10M17 7 7 17" /></svg>;
  return <svg {...common}><path d="m12 3 1.2 5.8L19 10l-5.8 1.2L12 17l-1.2-5.8L5 10l5.8-1.2L12 3ZM19 16l.5 2.5L22 19l-2.5.5L19 22l-.5-2.5L16 19l2.5-.5L19 16Z" /></svg>;
}

function StatusDot({ status }: { status: "done" | "active" | "pending" }) {
  if (status === "done") return <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#c6f45b] text-[#101410]"><Icon name="check" size={12} /></span>;
  if (status === "active") return <span className="relative flex h-5 w-5 items-center justify-center rounded-full border border-[#c6f45b]"><span className="h-1.5 w-1.5 rounded-full bg-[#c6f45b]" /></span>;
  return <span className="h-5 w-5 rounded-full border border-[#3d4541]" />;
}

export default function Home() {
  const [form, setForm] = useState<MigrationRequest>(sampleRequest);
  const [phase, setPhase] = useState<Phase>("review");
  const [workflowId, setWorkflowId] = useState("migration-demo-174");
  const [decision, setDecision] = useState<Decision>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setDecision(null);
    setLoading(true);
    setPhase("parsing");
    try {
      const result = await startMigration(form);
      setWorkflowId(result.workflow_id);
      setPhase("analyzing");
      await new Promise((resolve) => setTimeout(resolve, 700));
      setPhase("review");
    } catch (submissionError) {
      setError(submissionError instanceof Error ? submissionError.message : "Something went wrong.");
      setPhase("idle");
    } finally {
      setLoading(false);
    }
  };

  const decide = async (action: "APPROVE" | "REJECT") => {
    setError("");
    setLoading(true);
    try {
      await sendMigrationSignal(workflowId, action);
      setDecision(action);
    } catch (signalError) {
      setError(signalError instanceof Error ? signalError.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  const inputClass = "mt-2 w-full rounded-md border border-[#303836] bg-[#0d1010] px-3.5 py-3 text-sm text-[#edf0ed] placeholder:text-[#66706c] transition focus:border-[#c6f45b] focus:outline-none focus:ring-1 focus:ring-[#c6f45b]";
  const phaseStatus = (name: Phase): "done" | "active" | "pending" => {
    if (name === "parsing") return phase === "parsing" ? "active" : phase === "idle" ? "pending" : "done";
    if (name === "analyzing") return phase === "analyzing" ? "active" : phase === "review" ? "done" : "pending";
    return phase === "review" ? "active" : "pending";
  };

  return (
    <main className="relative min-h-screen overflow-hidden">
      <div className="grid-noise absolute inset-x-0 top-0 h-[480px]" />
      <header className="relative mx-auto flex max-w-[1440px] items-center justify-between border-b border-[#202523] px-5 py-5 sm:px-8 lg:px-12">
        <a href="/" className="flex items-center gap-2.5 text-sm font-semibold tracking-[-0.01em]">
          <span className="flex h-7 w-7 items-center justify-center rounded-md bg-[#c6f45b] text-[#101410]"><Icon name="shield" size={16} /></span>
          Safe Migration
        </a>
        <div className="flex items-center gap-4 text-xs text-[#84908b]">
          <span className="hidden sm:inline">Human-in-the-loop dependency upgrades</span>
          <span className="mono rounded border border-[#303836] px-2 py-1 text-[10px] uppercase tracking-[.12em] text-[#a9b2ad]">v0.1 beta</span>
        </div>
      </header>

      <div className="relative mx-auto max-w-[1440px] px-5 pb-20 pt-10 sm:px-8 sm:pt-14 lg:px-12">
        <div className="mb-10 max-w-2xl enter">
          <p className="mono mb-4 text-[11px] uppercase tracking-[.18em] text-[#c6f45b]">Migration control plane</p>
          <h1 className="max-w-xl text-4xl font-semibold leading-[1.05] tracking-[-.055em] text-[#f1f3ef] sm:text-5xl">Ship dependency changes with a second pair of eyes.</h1>
          <p className="mt-5 max-w-lg text-[15px] leading-7 text-[#8e9994]">Safe Migration parses your manifest, grounds its recommendations in security data, and puts you in control before anything changes.</p>
        </div>

        <div className="grid items-start gap-5 lg:grid-cols-[minmax(340px,400px)_minmax(0,1fr)]">
          <section className="enter enter-delay-1 rounded-lg border border-[#29302e] bg-[#111414]">
            <div className="border-b border-[#29302e] px-5 py-4">
              <div className="flex items-center justify-between">
                <div><p className="mono text-[10px] uppercase tracking-[.17em] text-[#84908b]">01 / Request</p><h2 className="mt-1 text-base font-medium">Start a migration</h2></div>
                <span className="flex h-7 w-7 items-center justify-center rounded-full border border-[#38413e] text-xs text-[#84908b]">1</span>
              </div>
            </div>
            <form onSubmit={submit} className="space-y-5 p-5">
              <label className="block text-sm text-[#dce2dc]" htmlFor="repo-url">
                GitHub repository URL <span className="text-[#c6f45b]">*</span>
                <input id="repo-url" required type="url" value={form.repo_url} onChange={(e) => setForm({ ...form, repo_url: e.target.value })} placeholder="https://github.com/org/repository" className={inputClass} />
              </label>
              <label className="block text-sm text-[#dce2dc]" htmlFor="config-path">
                Dependency / config file <span className="text-[#c6f45b]">*</span>
                <input id="config-path" required value={form.config_path} onChange={(e) => setForm({ ...form, config_path: e.target.value })} placeholder="e.g. requirements.txt" className={inputClass} />
                <span className="mt-2 block text-xs text-[#68736e]">Path from the repository root.</span>
              </label>
              <label className="block text-sm text-[#dce2dc]" htmlFor="project-type">
                Project type <span className="text-[#c6f45b]">*</span>
                <span className="relative mt-2 block">
                  <select id="project-type" required value={form.project_type} onChange={(e) => setForm({ ...form, project_type: e.target.value })} className={`${inputClass} appearance-none pr-10`}>
                    <option>Python</option><option>Node.js</option><option>Java</option><option>Go</option><option>Rust</option>
                  </select>
                  <span className="pointer-events-none absolute right-3.5 top-1/2 -translate-y-1/2 text-[#84908b]"><Icon name="chevron" size={15} /></span>
                </span>
              </label>
              {error && <p role="alert" className="rounded border border-[#6d3838] bg-[#2a1717] px-3 py-2 text-xs text-[#f39a9a]">{error}</p>}
              <button disabled={loading} className="flex w-full items-center justify-center gap-2 rounded-md bg-[#c6f45b] px-4 py-3 text-sm font-semibold text-[#101410] transition hover:bg-[#d4fa79] disabled:opacity-60">
                {loading ? "Working…" : phase === "review" ? "Run another analysis" : "Analyze dependencies"} {!loading && <Icon name="arrow" size={16} />}
              </button>
              <p className="text-center text-[11px] leading-5 text-[#68736e]">No changes are written until you approve the review.</p>
            </form>
          </section>

          <section className="min-w-0 enter enter-delay-2">
            <div className="mb-5 flex items-end justify-between">
              <div><p className="mono text-[10px] uppercase tracking-[.17em] text-[#84908b]">02 / Review workspace</p><h2 className="mt-1 text-lg font-medium">Review proposed changes</h2></div>
              <span className="mono hidden text-[10px] text-[#68736e] sm:block">{workflowId}</span>
            </div>
            <div className="mb-5 grid grid-cols-3 rounded-lg border border-[#29302e] bg-[#111414] p-4">
              {([{ key: "parsing", label: "Parsing manifest" }, { key: "analyzing", label: "AI analysis & security" }, { key: "review", label: "Human review" }] as const).map((item, index) => (
                <div key={item.key} className={`relative ${index < 2 ? "after:absolute after:left-[calc(50%+20px)] after:right-[-10px] after:top-2.5 after:h-px after:bg-[#303836]" : ""}`}>
                  <div className="relative z-10 flex items-center gap-2"><StatusDot status={phaseStatus(item.key)} /><span className={`hidden text-[11px] sm:inline ${phaseStatus(item.key) === "pending" ? "text-[#68736e]" : "text-[#dce2dc]"}`}>{item.label}</span></div>
                  {phase === item.key && <div className="running-line absolute left-7 right-2 top-[23px] h-px bg-[#c6f45b] sm:left-8" />}
                </div>
              ))}
            </div>

            {phase !== "review" ? (
              <div className="flex min-h-[460px] flex-col items-center justify-center rounded-lg border border-[#29302e] bg-[#111414] text-center">
                <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-full border border-[#536a2a] text-[#c6f45b]"><Icon name="spark" size={22} /></div>
                <h3 className="text-base font-medium">{phase === "parsing" ? "Reading your manifest…" : "Grounding upgrade recommendations…"}</h3>
                <p className="mt-2 max-w-xs text-sm leading-6 text-[#84908b]">{phase === "parsing" ? "Checking declared versions, lock files, and transitive dependencies." : "Comparing release notes with known security advisories."}</p>
              </div>
            ) : (
              <div className="space-y-5">
                <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_290px]">
                  <div className="min-w-0 rounded-lg border border-[#29302e] bg-[#111414]">
                    <div className="flex items-center justify-between border-b border-[#29302e] px-4 py-3">
                      <div><p className="mono text-[10px] uppercase tracking-[.14em] text-[#84908b]">Manifest diff</p><p className="mt-1 text-xs text-[#dce2dc]">{form.config_path || "requirements.txt"}</p></div>
                      <span className="mono text-[10px] text-[#c6f45b]">6 changes</span>
                    </div>
                    <div className="grid divide-y divide-[#29302e] md:grid-cols-2 md:divide-x md:divide-y-0">
                      <div><div className="border-b border-[#29302e] px-4 py-2 text-[10px] uppercase tracking-[.12em] text-[#68736e]">Current</div><pre className="overflow-x-auto p-4 text-[12px] leading-7 text-[#a2aca6]">{originalManifest}</pre></div>
                      <div><div className="border-b border-[#29302e] px-4 py-2 text-[10px] uppercase tracking-[.12em] text-[#c6f45b]">Proposed</div><pre className="overflow-x-auto p-4 text-[12px] leading-7 text-[#dbe7d0]">{upgradedManifest}</pre></div>
                    </div>
                  </div>
                  <div className="rounded-lg border border-[#29302e] bg-[#111414] p-4">
                    <div className="mb-4 flex items-center gap-2 text-[#c6f45b]"><Icon name="shield" size={17} /><span className="text-sm font-medium">Security grounding</span></div>
                    <p className="text-sm leading-6 text-[#aab4ae]">The proposed versions address <strong className="font-medium text-[#edf0ed]">3 known advisories</strong> without introducing new high-severity findings.</p>
                    <div className="mt-5 space-y-3 border-t border-[#29302e] pt-4">
                      <div className="flex justify-between text-xs"><span className="text-[#84908b]">Advisories resolved</span><span className="mono text-[#c6f45b]">3</span></div>
                      <div className="flex justify-between text-xs"><span className="text-[#84908b]">Breaking changes</span><span className="mono text-[#f0b84b]">1</span></div>
                      <div className="flex justify-between text-xs"><span className="text-[#84908b]">Confidence</span><span className="mono text-[#edf0ed]">94%</span></div>
                    </div>
                  </div>
                </div>
                <div className="rounded-lg border border-[#624b27] bg-[#17140e] p-4">
                  <div className="flex gap-3"><span className="mt-0.5 text-[#f0b84b]"><Icon name="alert" size={17} /></span><div><p className="text-sm font-medium text-[#f4d28c]">Review one breaking change</p><p className="mt-1 text-xs leading-5 text-[#bda475]"><span className="mono text-[#f0c874]">Django 4.2 → 5.0</span> removes <span className="mono">django.conf.urls.url</span>. Safe Migration found 2 references in your repository that need updating.</p></div></div>
                </div>
                <div className="flex flex-col gap-4 rounded-lg border border-[#29302e] bg-[#171b1a] p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div><p className="text-sm font-medium">{decision === "APPROVE" ? "Migration approved" : decision === "REJECT" ? "Migration rejected" : "Ready for your decision"}</p><p className="mt-1 text-xs text-[#84908b]">{decision ? "The workflow has been notified. You can safely close this review." : "Nothing will be written to the repository without your approval."}</p></div>
                  <div className="flex gap-2">
                    <button disabled={loading || decision !== null} onClick={() => decide("REJECT")} className="flex items-center justify-center gap-1.5 rounded-md border border-[#4b3434] px-3.5 py-2.5 text-xs font-medium text-[#eea0a0] transition hover:border-[#f17070] hover:bg-[#2a1717] disabled:opacity-45"><Icon name="close" size={14} /> Reject</button>
                    <button disabled={loading || decision !== null} onClick={() => decide("APPROVE")} className="flex items-center justify-center gap-1.5 rounded-md bg-[#c6f45b] px-3.5 py-2.5 text-xs font-semibold text-[#101410] transition hover:bg-[#d4fa79] disabled:opacity-45"><Icon name="check" size={14} /> Approve migration</button>
                  </div>
                </div>
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
