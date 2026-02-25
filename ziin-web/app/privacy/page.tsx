import Link from "next/link";

export default function PrivacyPage() {
  return (
    <main className="min-h-screen bg-[#171a2b] px-6 py-12 text-slate-100">
      <div className="mx-auto max-w-4xl space-y-8">
        <h1 className="text-3xl font-semibold tracking-tight">隱私權聲明</h1>

        <section className="space-y-3 text-slate-300">
          <h2 className="text-xl font-semibold text-slate-100">1. 聲明適用範圍</h2>
          <p>
            本聲明適用於 Ziin 網站、控制面板與 Discord 機器人服務（以下簡稱「本服務」）。
            使用本服務，即表示你同意本聲明內容。
          </p>
        </section>

        <section className="space-y-3 text-slate-300">
          <h2 className="text-xl font-semibold text-slate-100">2. 我們可能蒐集的資料</h2>
          <ul className="list-disc space-y-1 pl-6">
            <li>Discord 基本識別資訊（如 User ID、Guild ID、Channel ID）。</li>
            <li>你在本服務中設定的功能資料（通知頻道、訂閱清單、伺服器設定）。</li>
            <li>為了提供功能所需的事件紀錄（例如訊息異動、成員異動、語音事件）。</li>
          </ul>
        </section>

        <section className="space-y-3 text-slate-300">
          <h2 className="text-xl font-semibold text-slate-100">3. 資料使用目的</h2>
          <ul className="list-disc space-y-1 pl-6">
            <li>提供與維護 bot 功能與控制面板設定。</li>
            <li>改善服務品質、除錯與安全維護。</li>
            <li>處理使用者回報與技術支援。</li>
          </ul>
        </section>

        <section className="space-y-3 text-slate-300">
          <h2 className="text-xl font-semibold text-slate-100">4. 資料分享與揭露</h2>
          <p>
            我們不會出售你的資料。除依法要求、配合司法機關，或為維護服務安全之必要情況外，
            不會任意向第三方揭露可識別資料。
          </p>
        </section>

        <section className="space-y-3 text-slate-300">
          <h2 className="text-xl font-semibold text-slate-100">5. 資料保存與刪除</h2>
          <p>
            我們僅在提供服務所需期間保存資料。你可透過支援伺服器聯繫我們提出資料查詢或刪除請求，
            我們將在合理期間內處理。
          </p>
        </section>

        <section className="space-y-3 text-slate-300">
          <h2 className="text-xl font-semibold text-slate-100">6. 聲明更新</h2>
          <p>
            本聲明可能因功能、法規或營運需求更新。更新後版本將公布於本頁，
            你在更新後繼續使用本服務即視為同意更新內容。
          </p>
        </section>

        <section className="space-y-3 text-slate-300">
          <h2 className="text-xl font-semibold text-slate-100">7. 聯絡方式</h2>
          <p>
            若有隱私相關問題，請加入支援伺服器：
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
