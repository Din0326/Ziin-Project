import Link from "next/link";

export default function TermsPage() {
  return (
    <main className="min-h-screen bg-[#171a2b] px-6 py-12 text-slate-100">
      <div className="mx-auto max-w-4xl space-y-8">
        <h1 className="text-3xl font-semibold tracking-tight">使用條款</h1>

        <section className="space-y-3 text-slate-300">
          <h2 className="text-xl font-semibold text-slate-100">1. 服務說明</h2>
          <p>
            Ziin 提供 Discord 伺服器管理、事件紀錄與社群通知整合功能。
            我們保留調整、更新、暫停或終止部分功能之權利。
          </p>
        </section>

        <section className="space-y-3 text-slate-300">
          <h2 className="text-xl font-semibold text-slate-100">2. 使用者責任</h2>
          <ul className="list-disc space-y-1 pl-6">
            <li>你應確保有權在伺服器中安裝與設定本服務。</li>
            <li>你須妥善管理權限配置，避免未授權人員存取敏感設定。</li>
            <li>你不得利用本服務進行違法、騷擾、濫發或破壞性行為。</li>
          </ul>
        </section>

        <section className="space-y-3 text-slate-300">
          <h2 className="text-xl font-semibold text-slate-100">3. 禁止事項</h2>
          <ul className="list-disc space-y-1 pl-6">
            <li>反向工程、未授權存取、繞過限制或嘗試破壞系統安全。</li>
            <li>使用自動化手段惡意濫用 API、指令或通知機制。</li>
            <li>任何違反 Discord 平台規範與適用法律之行為。</li>
          </ul>
        </section>

        <section className="space-y-3 text-slate-300">
          <h2 className="text-xl font-semibold text-slate-100">4. 服務可用性與免責聲明</h2>
          <p>
            本服務以「現況」提供，可能因維護、第三方服務（如 Discord / YouTube / Twitch / X）
            或不可抗力因素中斷。我們不保證服務永不中斷或完全無誤。
          </p>
        </section>

        <section className="space-y-3 text-slate-300">
          <h2 className="text-xl font-semibold text-slate-100">5. 內容與責任限制</h2>
          <p>
            伺服器管理行為與資料設定由使用者自行負責。
            對於因誤設、第三方平台變動或外部因素造成的損失，我們在法律允許範圍內不承擔間接損害責任。
          </p>
        </section>

        <section className="space-y-3 text-slate-300">
          <h2 className="text-xl font-semibold text-slate-100">6. 條款更新</h2>
          <p>
            我們可能依營運與法規需求更新本條款。更新後將公告於本頁，
            你在更新後繼續使用本服務即視為同意新條款。
          </p>
        </section>

        <section className="space-y-3 text-slate-300">
          <h2 className="text-xl font-semibold text-slate-100">7. 聯絡方式</h2>
          <p>
            若你對條款有疑問，請加入支援伺服器：
            <a
              href="https://discord.gg/EtQX9RB9Xr"
              target="_blank"
              rel="noreferrer"
              className="ml-1 text-indigo-300 hover:text-indigo-200"
            >
              discord.gg/EtQX9RB9Xr
            </a>
          </p>
        </section>

        <div>
          <Link href="/" className="text-indigo-300 transition hover:text-indigo-200">返回首頁</Link>
        </div>
      </div>
    </main>
  );
}
