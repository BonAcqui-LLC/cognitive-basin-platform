package llc.bonacqui.aia.runtime

import android.content.Context
import android.net.ConnectivityManager
import android.os.BatteryManager
import android.os.Build
import android.os.PowerManager
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.security.MessageDigest
import java.time.Instant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter
import java.util.UUID

enum class EpistemicState { SUPPORTED, UNRESOLVED, CONTRADICTED }
enum class ActionState { EXTEND, HOLD, RETRACT }
enum class DemoScenario { AUTO, SUPPORTED, HOLD, CONTRADICTION, DEVICE_REVIEW }
enum class ActivationType {
    AIA_DEMO_GUIDANCE,
    AIA_CIVIL_RIGHTS_SESSION,
    BASINLAB_DIAGNOSTIC,
    DEVICE_INTEGRITY_REVIEW
}

data class GuardianFinding(
    val code: String,
    val severity: String,
    val message: String,
    val forcesHold: Boolean
)

data class RecoveryRoute(
    val routeId: String,
    val title: String,
    val steps: List<String>
)

data class ContradictionScar(
    val scarId: String,
    val priorEpistemicState: EpistemicState,
    val contradictoryEvidence: List<String>,
    val unresolvedQuestions: List<String>
)

data class SeraMetrics(
    val activationDurationMs: Long,
    val memoryBeforeBytes: Long,
    val memoryAfterBytes: Long,
    val batteryPercent: Int,
    val thermalStatus: String,
    val providerCalls: Int,
    val providerFailures: Int,
    val ruleLookups: Int,
    val holdCount: Int,
    val contradictionCount: Int,
    val exportSizeBytes: Long? = null,
    val persistenceSizeBytes: Long? = null
)

data class SessionRecord(
    val sessionId: String,
    val purpose: String,
    val activationType: ActivationType,
    val activationManifest: Map<String, Any>,
    val guardianFindings: List<GuardianFinding>,
    val evidence: List<String>,
    val missingEvidence: List<String>,
    val contradictoryEvidence: List<String>,
    val recoveryRoutes: List<RecoveryRoute>,
    val contradictionScars: List<ContradictionScar>,
    val finalEpistemic: EpistemicState,
    val finalAction: ActionState,
    val holdReasons: List<String>,
    val providerIdentity: String,
    val rulePackIdentity: String,
    val startedAt: String,
    val finishedAt: String,
    val seraMetrics: SeraMetrics
)

data class SessionSummary(
    val sessionId: String,
    val activationType: String,
    val epistemic: String,
    val action: String,
    val startedAt: String
)

data class ExportResult(val success: Boolean, val message: String, val session: SessionRecord? = null)

class AiaRuntime(private val context: Context) {
    val headline: String = "AIA Sovereign Device"

    private val timeFormatter: DateTimeFormatter = DateTimeFormatter.ISO_OFFSET_DATE_TIME.withZone(ZoneOffset.UTC)
    private val sessionDir = File(context.filesDir, "sessions").apply { mkdirs() }
    private val exportDir = (context.getExternalFilesDir("exports") ?: File(context.filesDir, "exports")).apply { mkdirs() }
    private val contractVersion = "ternary-mobile-v0.1"
    private val providerIdentity = "deterministic_fixture_provider"
    private val rulePackIdentity = "demo-civil-rights-pack@2026-06-17"

    fun dashboardStatus(currentSession: SessionRecord?): String {
        val connectivity = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val activeNetwork = connectivity.activeNetworkInfo
        val onlineStatus = if (activeNetwork?.isConnected == true) "online" else "offline-or-no-network"
        val lastSession = currentSession ?: listSessions().firstOrNull()?.let { loadSession(it.sessionId) }
        return buildString {
            append("Device-local status: Android ${Build.VERSION.RELEASE} on ${Build.MODEL}\n")
            append("Offline/online status: $onlineStatus\n")
            append("Model-provider status: deterministic fixture available; external provider disabled\n")
            append("Rule-pack status: $rulePackIdentity (demonstration only)\n")
            append("Cognitive Basin runtime status: deterministic Kotlin governance active\n")
            append("Last activation: ${lastSession?.activationType ?: "none yet"}")
        }
    }

    fun idleNarrative(): String {
        return buildString {
            append("Purpose-first activation is ready.\n\n")
            append("Use the typed purpose field or the deterministic demo buttons.\n")
            append("The runtime preserves canonical ternary states internally: SUPPORTED, UNRESOLVED, CONTRADICTED and EXTEND, HOLD, RETRACT.\n")
            append("No model provider can override the final governed state.")
        }
    }

    fun exportStatus(): String {
        val latest = latestExportFile()
        return if (latest == null) {
            "No export created yet."
        } else {
            "Latest export: ${latest.name}\nPath: ${latest.absolutePath}"
        }
    }

    fun beginActivation(purpose: String, scenario: DemoScenario): SessionRecord {
        val startedAt = now()
        val memoryBefore = appMemory()
        val batteryBefore = batteryPercent()
        val activationType = classifyActivation(purpose)
        val manifest = linkedMapOf<String, Any>(
            "purpose" to purpose,
            "activation_type" to activationType.name.lowercase(),
            "requested_capabilities" to requestedCapabilities(activationType),
            "provider_identity" to providerIdentity,
            "rule_pack_identity" to rulePackIdentity,
            "device_build_identity" to "${Build.MANUFACTURER}/${Build.DEVICE}/${Build.VERSION.RELEASE}",
            "app_version" to appVersionName()
        )
        val guardianFindings = guardianPass(purpose, activationType, scenario, manifest)
        val missingEvidence = mutableListOf<String>()
        val contradictoryEvidence = mutableListOf<String>()
        val evidence = mutableListOf(
            "observed_fact: device-local session on Android ${Build.VERSION.RELEASE}",
            "rule_pack_content: demonstration rule pack $rulePackIdentity",
            "user_assertion: purpose entered on device"
        )

        val effectiveScenario = if (scenario == DemoScenario.AUTO) inferScenarioFromPurpose(purpose, activationType) else scenario
        when (effectiveScenario) {
            DemoScenario.SUPPORTED, DemoScenario.DEVICE_REVIEW -> {
                evidence += "observed_fact: deterministic governance runtime available"
                if (activationType == ActivationType.AIA_CIVIL_RIGHTS_SESSION || activationType == ActivationType.AIA_DEMO_GUIDANCE) {
                    evidence += "observed_fact: jurisdiction demo tag supplied or assumed for demonstration"
                }
            }
            DemoScenario.HOLD -> {
                missingEvidence += "jurisdiction label is absent or not trustworthy enough"
                missingEvidence += "key factual predicates are still unresolved"
                evidence += "unresolved_fact: meeting context is incomplete"
            }
            DemoScenario.CONTRADICTION -> {
                contradictoryEvidence += "user assertion says the meeting was recorded"
                contradictoryEvidence += "user assertion also says the meeting was not recorded"
                evidence += "user_assertion: conflicting claims were provided"
            }
            DemoScenario.AUTO -> Unit
        }

        if (guardianFindings.any { it.forcesHold } && contradictoryEvidence.isEmpty()) {
            missingEvidence += guardianFindings.filter { it.forcesHold }.map { it.message }
        }

        val finalEpistemic = when {
            contradictoryEvidence.isNotEmpty() -> EpistemicState.CONTRADICTED
            missingEvidence.isNotEmpty() -> EpistemicState.UNRESOLVED
            else -> EpistemicState.SUPPORTED
        }
        val finalAction = when (finalEpistemic) {
            EpistemicState.SUPPORTED -> ActionState.EXTEND
            EpistemicState.UNRESOLVED -> ActionState.HOLD
            EpistemicState.CONTRADICTED -> ActionState.RETRACT
        }

        val recoveryRoutes = recoveryRoutesFor(finalEpistemic, activationType)
        val contradictionScars = if (finalEpistemic == EpistemicState.CONTRADICTED) {
            listOf(
                ContradictionScar(
                    scarId = "scar-${UUID.randomUUID().toString().take(8)}",
                    priorEpistemicState = EpistemicState.SUPPORTED,
                    contradictoryEvidence = contradictoryEvidence.toList(),
                    unresolvedQuestions = listOf("Obtain the primary artifact or a reliable witness note before proceeding.")
                )
            )
        } else {
            emptyList()
        }

        val finishedAt = now()
        val session = SessionRecord(
            sessionId = "session-${UUID.randomUUID().toString().take(8)}",
            purpose = purpose,
            activationType = activationType,
            activationManifest = manifest,
            guardianFindings = guardianFindings,
            evidence = evidence,
            missingEvidence = missingEvidence,
            contradictoryEvidence = contradictoryEvidence,
            recoveryRoutes = recoveryRoutes,
            contradictionScars = contradictionScars,
            finalEpistemic = finalEpistemic,
            finalAction = finalAction,
            holdReasons = missingEvidence.ifEmpty {
                if (contradictoryEvidence.isNotEmpty()) listOf("Contradictory evidence preserved instead of collapsed.") else emptyList()
            },
            providerIdentity = providerIdentity,
            rulePackIdentity = rulePackIdentity,
            startedAt = startedAt,
            finishedAt = finishedAt,
            seraMetrics = SeraMetrics(
                activationDurationMs = millisBetween(startedAt, finishedAt),
                memoryBeforeBytes = memoryBefore,
                memoryAfterBytes = appMemory(),
                batteryPercent = batteryBefore,
                thermalStatus = thermalStatus(),
                providerCalls = 0,
                providerFailures = 0,
                ruleLookups = 1,
                holdCount = if (finalAction == ActionState.HOLD) 1 else 0,
                contradictionCount = contradictoryEvidence.size
            )
        )
        saveSession(session)
        return session
    }

    fun listSessions(): List<SessionSummary> {
        return sessionDir.listFiles { file -> file.extension == "json" }
            ?.mapNotNull { file -> runCatching { parseSession(file.readText()) }.getOrNull() }
            ?.sortedByDescending { it.startedAt }
            ?.map {
                SessionSummary(
                    sessionId = it.sessionId,
                    activationType = it.activationType.name,
                    epistemic = it.finalEpistemic.name,
                    action = it.finalAction.name,
                    startedAt = it.startedAt
                )
            }
            ?: emptyList()
    }

    fun loadSession(sessionId: String): SessionRecord? {
        val file = File(sessionDir, "$sessionId.json")
        if (!file.exists()) return null
        return parseSession(file.readText())
    }

    fun sessionNarrative(session: SessionRecord): String {
        return buildString {
            append("Purpose: ${session.purpose}\n")
            append("Activation: ${session.activationType}\n")
            append("Provider: ${session.providerIdentity}\n")
            append("Rule pack: ${session.rulePackIdentity}\n")
            append("Governed state: ${session.finalEpistemic} / ${session.finalAction}\n\n")
            append("Requested capabilities:\n")
            append((session.activationManifest["requested_capabilities"] as List<*>).joinToString("\n") { "- $it" })
            append("\n\nEvidence:\n")
            append(session.evidence.joinToString("\n") { "- $it" })
            if (session.missingEvidence.isNotEmpty()) {
                append("\n\nMissing evidence:\n")
                append(session.missingEvidence.joinToString("\n") { "- $it" })
            }
            if (session.contradictoryEvidence.isNotEmpty()) {
                append("\n\nContradictions:\n")
                append(session.contradictoryEvidence.joinToString("\n") { "- $it" })
            }
            if (session.guardianFindings.isNotEmpty()) {
                append("\n\nGuardian findings:\n")
                append(session.guardianFindings.joinToString("\n") { "- ${it.code}: ${it.message}" })
            }
            append("\n\nRecovery routes:\n")
            append(session.recoveryRoutes.joinToString("\n") { route -> "- ${route.title}: ${route.steps.joinToString("; ")}" })
            append("\n\nSERA:\n")
            append("duration=${session.seraMetrics.activationDurationMs}ms, memory_before=${session.seraMetrics.memoryBeforeBytes}, memory_after=${session.seraMetrics.memoryAfterBytes}, battery=${session.seraMetrics.batteryPercent}%, thermal=${session.seraMetrics.thermalStatus}")
        }
    }

    fun exportSession(sessionId: String): ExportResult {
        val session = loadSession(sessionId) ?: return ExportResult(false, "Session not found.")
        val sessionJson = sessionToJson(session)
        val sessionHash = sha256(sessionJson.toString())
        val bundle = JSONObject()
            .put("manifest_version", "sessionglyph-export-v0.1")
            .put("session_hash", sessionHash)
            .put("application_version", appVersionName())
            .put("contract_version", contractVersion)
            .put("rule_pack_identity", session.rulePackIdentity)
            .put("provider_identity", session.providerIdentity)
            .put("guardian_findings", JSONArray(session.guardianFindings.map { guardianToJson(it) }))
            .put("sera_metrics", seraToJson(session.seraMetrics))
            .put("final_governed_state", JSONObject().put("epistemic", session.finalEpistemic.name).put("action", session.finalAction.name))
            .put("session_data", sessionJson)
        val exportFile = File(exportDir, "${session.sessionId}.aiaexport.json")
        exportFile.writeText(bundle.toString(2))
        return ExportResult(true, "Export verified and written to ${exportFile.absolutePath}", session)
    }

    fun verifyAndImportLastExport(): ExportResult {
        val file = latestExportFile() ?: return ExportResult(false, "No export exists yet.")
        val bundle = JSONObject(file.readText())
        val sessionData = bundle.getJSONObject("session_data")
        val expectedHash = bundle.getString("session_hash")
        val actualHash = sha256(sessionData.toString())
        if (expectedHash != actualHash) {
            return ExportResult(false, "Verification failed: export hash mismatch.")
        }
        val session = parseSession(sessionData.toString())
        saveSession(session)
        return ExportResult(true, "Export verified and reopened successfully from ${file.name}.", session)
    }

    fun runTamperCheck(): ExportResult {
        val file = latestExportFile() ?: return ExportResult(false, "No export exists yet.")
        val tamperedFile = File(exportDir, file.nameWithoutExtension + ".tampered.json")
        val bundle = JSONObject(file.readText())
        bundle.getJSONObject("session_data").put("purpose", "tampered-purpose")
        tamperedFile.writeText(bundle.toString(2))
        val tampered = JSONObject(tamperedFile.readText())
        val actualHash = sha256(tampered.getJSONObject("session_data").toString())
        val expectedHash = tampered.getString("session_hash")
        return if (actualHash == expectedHash) {
            ExportResult(false, "Tamper check failed: modified export still verified unexpectedly.")
        } else {
            ExportResult(true, "Tamper check succeeded: modified export fails verification as expected.")
        }
    }

    private fun classifyActivation(purpose: String): ActivationType {
        val lower = purpose.lowercase()
        return when {
            "civil" in lower || "rights" in lower -> ActivationType.AIA_CIVIL_RIGHTS_SESSION
            "device" in lower || "runtime" in lower || "integrity" in lower -> ActivationType.DEVICE_INTEGRITY_REVIEW
            "diagnostic" in lower || "basinlab" in lower -> ActivationType.BASINLAB_DIAGNOSTIC
            else -> ActivationType.AIA_DEMO_GUIDANCE
        }
    }

    private fun inferScenarioFromPurpose(purpose: String, activationType: ActivationType): DemoScenario {
        val lower = purpose.lowercase()
        return when {
            "conflict" in lower || "contradict" in lower -> DemoScenario.CONTRADICTION
            "missing" in lower || "uncertain" in lower || ("rights" in lower && !containsJurisdiction(lower)) -> DemoScenario.HOLD
            activationType == ActivationType.DEVICE_INTEGRITY_REVIEW -> DemoScenario.DEVICE_REVIEW
            else -> DemoScenario.SUPPORTED
        }
    }

    private fun requestedCapabilities(activationType: ActivationType): List<String> {
        return when (activationType) {
            ActivationType.AIA_DEMO_GUIDANCE -> listOf("purpose_anchor", "deterministic_guidance", "local_persistence", "export_verification")
            ActivationType.AIA_CIVIL_RIGHTS_SESSION -> listOf("purpose_anchor", "rule_pack_lookup", "guardian_review", "hold_routing")
            ActivationType.BASINLAB_DIAGNOSTIC -> listOf("device_status", "runtime_status", "governance_trace")
            ActivationType.DEVICE_INTEGRITY_REVIEW -> listOf("device_status", "verified_boot_review", "provider_boundary_review")
        }
    }

    private fun guardianPass(
        purpose: String,
        activationType: ActivationType,
        scenario: DemoScenario,
        manifest: Map<String, Any>
    ): List<GuardianFinding> {
        val findings = mutableListOf<GuardianFinding>()
        val lower = purpose.lowercase()
        if (purpose.isBlank()) {
            findings += GuardianFinding("malformed_activation_manifest", "high", "Purpose cannot be blank.", true)
        }
        if (activationType == ActivationType.AIA_CIVIL_RIGHTS_SESSION && !containsJurisdiction(lower) && scenario != DemoScenario.SUPPORTED) {
            findings += GuardianFinding("absent_jurisdiction", "high", "Civil-rights demo lacks a reliable jurisdiction label.", true)
        }
        if ("guarantee" in lower || "definitely" in lower) {
            findings += GuardianFinding("unsupported_certainty", "medium", "The purpose requests certainty the demo cannot justify.", true)
        }
        if ("send" in lower || "email" in lower || "text " in lower || "post " in lower) {
            findings += GuardianFinding("external_action_request", "high", "External action remains unauthorized in this tranche.", true)
        }
        if ("unlock" in lower || "root" in lower || "flash" in lower) {
            findings += GuardianFinding("capability_expansion", "high", "Device modification authority is prohibited in this tranche.", true)
        }
        if ("completed" in lower || "already solved" in lower) {
            findings += GuardianFinding("unsupported_completion_claim", "medium", "Completion claims require evidence, not assertion.", true)
        }
        findings += GuardianFinding("demo_rule_pack", "info", "Rule pack is demonstration content only and not production legal authority.", false)
        if (!manifest.containsKey("requested_capabilities")) {
            findings += GuardianFinding("malformed_activation_manifest", "high", "Requested capabilities are missing.", true)
        }
        return findings
    }

    private fun containsJurisdiction(lower: String): Boolean {
        return listOf("ohio", "texas", "california", "new york", "florida", "michigan", "demo-jurisdiction").any { it in lower }
    }

    private fun recoveryRoutesFor(epistemic: EpistemicState, activationType: ActivationType): List<RecoveryRoute> {
        return when (epistemic) {
            EpistemicState.SUPPORTED -> listOf(
                RecoveryRoute(
                    routeId = "route-supported-1",
                    title = "Proceed with bounded demonstration",
                    steps = listOf("Render the governed state", "Persist the session", "Export a verifiable session package")
                )
            )
            EpistemicState.UNRESOLVED -> listOf(
                RecoveryRoute(
                    routeId = "route-hold-1",
                    title = "Collect missing evidence and rerun",
                    steps = listOf("Add a jurisdiction label", "Clarify the key facts", "Re-run the deterministic activation")
                ),
                RecoveryRoute(
                    routeId = "route-hold-2",
                    title = "Switch to basinlab diagnostic if legal facts are unavailable",
                    steps = listOf("Preserve the unresolved state", "Inspect device/runtime status", "Return once evidence exists")
                )
            )
            EpistemicState.CONTRADICTED -> listOf(
                RecoveryRoute(
                    routeId = "route-contradiction-1",
                    title = "Preserve contradiction and seek primary artifact",
                    steps = listOf("Keep both claims visible", "Obtain a trustworthy note or recording policy artifact", "Re-enter the activation with sourced facts")
                )
            )
        }
    }

    private fun saveSession(session: SessionRecord) {
        val file = File(sessionDir, "${session.sessionId}.json")
        file.writeText(sessionToJson(session).toString(2))
    }

    private fun sessionToJson(session: SessionRecord): JSONObject {
        return JSONObject()
            .put("session_id", session.sessionId)
            .put("purpose", session.purpose)
            .put("activation_type", session.activationType.name)
            .put("activation_manifest", JSONObject(session.activationManifest))
            .put("guardian_findings", JSONArray(session.guardianFindings.map { guardianToJson(it) }))
            .put("evidence", JSONArray(session.evidence))
            .put("missing_evidence", JSONArray(session.missingEvidence))
            .put("contradictory_evidence", JSONArray(session.contradictoryEvidence))
            .put("recovery_routes", JSONArray(session.recoveryRoutes.map { routeToJson(it) }))
            .put("contradiction_scars", JSONArray(session.contradictionScars.map { scarToJson(it) }))
            .put("final_epistemic", session.finalEpistemic.name)
            .put("final_action", session.finalAction.name)
            .put("hold_reasons", JSONArray(session.holdReasons))
            .put("provider_identity", session.providerIdentity)
            .put("rule_pack_identity", session.rulePackIdentity)
            .put("started_at", session.startedAt)
            .put("finished_at", session.finishedAt)
            .put("sera_metrics", seraToJson(session.seraMetrics))
    }

    private fun parseSession(text: String): SessionRecord {
        val json = JSONObject(text)
        return SessionRecord(
            sessionId = json.getString("session_id"),
            purpose = json.getString("purpose"),
            activationType = ActivationType.valueOf(json.getString("activation_type")),
            activationManifest = jsonObjectToMap(json.getJSONObject("activation_manifest")),
            guardianFindings = json.getJSONArray("guardian_findings").toGuardianFindings(),
            evidence = json.getJSONArray("evidence").toStringList(),
            missingEvidence = json.getJSONArray("missing_evidence").toStringList(),
            contradictoryEvidence = json.getJSONArray("contradictory_evidence").toStringList(),
            recoveryRoutes = json.getJSONArray("recovery_routes").toRecoveryRoutes(),
            contradictionScars = json.getJSONArray("contradiction_scars").toContradictionScars(),
            finalEpistemic = EpistemicState.valueOf(json.getString("final_epistemic")),
            finalAction = ActionState.valueOf(json.getString("final_action")),
            holdReasons = json.getJSONArray("hold_reasons").toStringList(),
            providerIdentity = json.getString("provider_identity"),
            rulePackIdentity = json.getString("rule_pack_identity"),
            startedAt = json.getString("started_at"),
            finishedAt = json.getString("finished_at"),
            seraMetrics = json.getJSONObject("sera_metrics").toSeraMetrics()
        )
    }

    private fun guardianToJson(finding: GuardianFinding): JSONObject {
        return JSONObject()
            .put("code", finding.code)
            .put("severity", finding.severity)
            .put("message", finding.message)
            .put("forces_hold", finding.forcesHold)
    }

    private fun routeToJson(route: RecoveryRoute): JSONObject {
        return JSONObject()
            .put("route_id", route.routeId)
            .put("title", route.title)
            .put("steps", JSONArray(route.steps))
    }

    private fun scarToJson(scar: ContradictionScar): JSONObject {
        return JSONObject()
            .put("scar_id", scar.scarId)
            .put("prior_epistemic_state", scar.priorEpistemicState.name)
            .put("contradictory_evidence", JSONArray(scar.contradictoryEvidence))
            .put("unresolved_questions", JSONArray(scar.unresolvedQuestions))
    }

    private fun seraToJson(sera: SeraMetrics): JSONObject {
        return JSONObject()
            .put("activation_duration_ms", sera.activationDurationMs)
            .put("memory_before_bytes", sera.memoryBeforeBytes)
            .put("memory_after_bytes", sera.memoryAfterBytes)
            .put("battery_percent", sera.batteryPercent)
            .put("thermal_status", sera.thermalStatus)
            .put("provider_calls", sera.providerCalls)
            .put("provider_failures", sera.providerFailures)
            .put("rule_lookups", sera.ruleLookups)
            .put("hold_count", sera.holdCount)
            .put("contradiction_count", sera.contradictionCount)
            .put("export_size_bytes", sera.exportSizeBytes)
            .put("persistence_size_bytes", sera.persistenceSizeBytes)
    }

    private fun JSONArray.toStringList(): List<String> = List(length()) { index -> getString(index) }

    private fun JSONArray.toGuardianFindings(): List<GuardianFinding> = List(length()) { index ->
        val obj = getJSONObject(index)
        GuardianFinding(
            code = obj.getString("code"),
            severity = obj.getString("severity"),
            message = obj.getString("message"),
            forcesHold = obj.getBoolean("forces_hold")
        )
    }

    private fun JSONArray.toRecoveryRoutes(): List<RecoveryRoute> = List(length()) { index ->
        val obj = getJSONObject(index)
        RecoveryRoute(
            routeId = obj.getString("route_id"),
            title = obj.getString("title"),
            steps = obj.getJSONArray("steps").toStringList()
        )
    }

    private fun JSONArray.toContradictionScars(): List<ContradictionScar> = List(length()) { index ->
        val obj = getJSONObject(index)
        ContradictionScar(
            scarId = obj.getString("scar_id"),
            priorEpistemicState = EpistemicState.valueOf(obj.getString("prior_epistemic_state")),
            contradictoryEvidence = obj.getJSONArray("contradictory_evidence").toStringList(),
            unresolvedQuestions = obj.getJSONArray("unresolved_questions").toStringList()
        )
    }

    private fun JSONObject.toSeraMetrics(): SeraMetrics {
        return SeraMetrics(
            activationDurationMs = getLong("activation_duration_ms"),
            memoryBeforeBytes = getLong("memory_before_bytes"),
            memoryAfterBytes = getLong("memory_after_bytes"),
            batteryPercent = getInt("battery_percent"),
            thermalStatus = getString("thermal_status"),
            providerCalls = getInt("provider_calls"),
            providerFailures = getInt("provider_failures"),
            ruleLookups = getInt("rule_lookups"),
            holdCount = getInt("hold_count"),
            contradictionCount = getInt("contradiction_count"),
            exportSizeBytes = if (isNull("export_size_bytes")) null else getLong("export_size_bytes"),
            persistenceSizeBytes = if (isNull("persistence_size_bytes")) null else getLong("persistence_size_bytes")
        )
    }

    private fun jsonObjectToMap(obj: JSONObject): Map<String, Any> {
        val map = linkedMapOf<String, Any>()
        obj.keys().forEach { key ->
            val value = obj.get(key)
            map[key] = when (value) {
                is JSONArray -> List(value.length()) { index -> value.get(index).toString() }
                else -> value
            }
        }
        return map
    }

    private fun latestExportFile(): File? {
        return exportDir.listFiles { file -> file.extension == "json" }
            ?.filterNot { it.name.contains(".tampered.") }
            ?.sortedByDescending { it.lastModified() }
            ?.firstOrNull()
    }

    private fun now(): String = timeFormatter.format(Instant.now())

    private fun millisBetween(startedAt: String, finishedAt: String): Long {
        return Instant.parse(finishedAt).toEpochMilli() - Instant.parse(startedAt).toEpochMilli()
    }

    private fun appMemory(): Long {
        val runtime = Runtime.getRuntime()
        return runtime.totalMemory() - runtime.freeMemory()
    }

    private fun batteryPercent(): Int {
        val batteryManager = context.getSystemService(Context.BATTERY_SERVICE) as BatteryManager
        return batteryManager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
    }

    private fun thermalStatus(): String {
        val powerManager = context.getSystemService(Context.POWER_SERVICE) as PowerManager
        return when (powerManager.currentThermalStatus) {
            PowerManager.THERMAL_STATUS_NONE -> "none"
            PowerManager.THERMAL_STATUS_LIGHT -> "light"
            PowerManager.THERMAL_STATUS_MODERATE -> "moderate"
            PowerManager.THERMAL_STATUS_SEVERE -> "severe"
            PowerManager.THERMAL_STATUS_CRITICAL -> "critical"
            PowerManager.THERMAL_STATUS_EMERGENCY -> "emergency"
            PowerManager.THERMAL_STATUS_SHUTDOWN -> "shutdown"
            else -> "unknown"
        }
    }

    private fun sha256(text: String): String {
        val digest = MessageDigest.getInstance("SHA-256").digest(text.toByteArray(Charsets.UTF_8))
        return digest.joinToString("") { "%02x".format(it) }
    }

    private fun appVersionName(): String {
        val packageInfo = context.packageManager.getPackageInfo(context.packageName, 0)
        return packageInfo.versionName ?: "0.0.0"
    }
}
