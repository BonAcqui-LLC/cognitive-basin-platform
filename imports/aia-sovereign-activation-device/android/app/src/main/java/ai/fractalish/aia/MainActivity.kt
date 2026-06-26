package llc.bonacqui.aia

import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import llc.bonacqui.aia.runtime.AiaRuntime
import llc.bonacqui.aia.runtime.DemoScenario
import llc.bonacqui.aia.runtime.SessionRecord

class MainActivity : AppCompatActivity() {
    private lateinit var runtime: AiaRuntime
    private var currentSession: SessionRecord? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        runtime = AiaRuntime(this)

        val headlineText = findViewById<TextView>(R.id.headlineText)
        val statusText = findViewById<TextView>(R.id.statusText)
        val purposeInput = findViewById<EditText>(R.id.purposeInput)
        val decisionText = findViewById<TextView>(R.id.decisionText)
        val detailText = findViewById<TextView>(R.id.detailText)
        val exportText = findViewById<TextView>(R.id.exportText)
        val sessionsContainer = findViewById<LinearLayout>(R.id.sessionsContainer)
        val refreshButton = findViewById<Button>(R.id.refreshButton)
        val beginButton = findViewById<Button>(R.id.beginButton)
        val supportedButton = findViewById<Button>(R.id.supportedButton)
        val holdButton = findViewById<Button>(R.id.holdButton)
        val contradictionButton = findViewById<Button>(R.id.contradictionButton)
        val deviceReviewButton = findViewById<Button>(R.id.deviceReviewButton)
        val exportButton = findViewById<Button>(R.id.exportButton)
        val importButton = findViewById<Button>(R.id.importButton)
        val tamperButton = findViewById<Button>(R.id.tamperButton)

        headlineText.text = runtime.headline

        fun renderSessions() {
            sessionsContainer.removeAllViews()
            val summaries = runtime.listSessions()
            if (summaries.isEmpty()) {
                val empty = TextView(this).apply {
                    text = "No persisted sessions yet."
                    setTextColor(0xFF314038.toInt())
                }
                sessionsContainer.addView(empty)
                return
            }
            summaries.forEach { summary ->
                val button = Button(this).apply {
                    text = "${summary.activationType}  ${summary.epistemic}/${summary.action}\n${summary.startedAt}"
                    isAllCaps = false
                    setOnClickListener {
                        currentSession = runtime.loadSession(summary.sessionId)
                        currentSession?.let { session ->
                            decisionText.text = "${session.finalEpistemic} / ${session.finalAction}"
                            detailText.text = runtime.sessionNarrative(session)
                        }
                    }
                }
                sessionsContainer.addView(button)
            }
        }

        fun renderDashboard() {
            statusText.text = runtime.dashboardStatus(currentSession)
            decisionText.text = currentSession?.let { "${it.finalEpistemic} / ${it.finalAction}" } ?: "READY / LOCAL"
            detailText.text = currentSession?.let { runtime.sessionNarrative(it) } ?: runtime.idleNarrative()
            exportText.text = runtime.exportStatus()
            renderSessions()
        }

        fun runScenario(scenario: DemoScenario, fallbackPurpose: String) {
            val purpose = purposeInput.text?.toString()?.trim().orEmpty().ifBlank { fallbackPurpose }
            currentSession = runtime.beginActivation(purpose, scenario)
            renderDashboard()
        }

        refreshButton.setOnClickListener { renderDashboard() }
        beginButton.setOnClickListener {
            runScenario(
                DemoScenario.AUTO,
                "Help me understand my rights during this interaction."
            )
        }
        supportedButton.setOnClickListener {
            runScenario(
                DemoScenario.SUPPORTED,
                "Start a demo guidance session for Ohio workplace note-taking rights."
            )
        }
        holdButton.setOnClickListener {
            runScenario(
                DemoScenario.HOLD,
                "Review this employment meeting with missing jurisdiction and incomplete facts."
            )
        }
        contradictionButton.setOnClickListener {
            runScenario(
                DemoScenario.CONTRADICTION,
                "Review conflicting statements about whether the meeting was recorded and not recorded."
            )
        }
        deviceReviewButton.setOnClickListener {
            runScenario(
                DemoScenario.DEVICE_REVIEW,
                "Inspect the device and runtime state."
            )
        }
        exportButton.setOnClickListener {
            val message = currentSession?.let { runtime.exportSession(it.sessionId).message }
                ?: "No session selected for export."
            renderDashboard()
            exportText.text = message
        }
        importButton.setOnClickListener {
            val result = runtime.verifyAndImportLastExport()
            currentSession = result.session ?: currentSession
            renderDashboard()
            exportText.text = result.message
        }
        tamperButton.setOnClickListener {
            val result = runtime.runTamperCheck()
            renderDashboard()
            exportText.text = result.message
        }

        renderDashboard()
    }
}
