package com.padippupal.app

import android.annotation.SuppressLint
import android.view.View
import android.util.Log
import android.webkit.ConsoleMessage
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import org.json.JSONObject

/**
 * Chapter-only PixiJS canvas. The scene changes with the active tutor synthesis
 * step; all other chapters continue using the existing visual renderer.
 */
@SuppressLint("SetJavaScriptEnabled")
@Composable
internal fun BeyondEarthPixiCanvas(
    step: Int,
    subtype: String,
    compact: Boolean,
    modifier: Modifier = Modifier
) {
    val webViewState = remember { mutableStateOf<WebView?>(null) }
    val safeStep = step.coerceIn(0, 7)

    AndroidView(
        modifier = modifier.height(if (compact) 150.dp else 190.dp),
        factory = { context ->
            WebView(context).apply {
                // WebView's hardware-composited surface blanked the enclosing Compose lesson
                // on the API 35 emulator (semantics tree remained populated, screenshots were
                // paper-colored). Keep this small inline drawing in the software layer so the
                // caption and its word-highlight span remain visible above it.
                setLayerType(View.LAYER_TYPE_SOFTWARE, null)
                settings.javaScriptEnabled = true
                settings.domStorageEnabled = false
                settings.allowFileAccess = true
                settings.allowContentAccess = false
                settings.setSupportZoom(false)
                settings.builtInZoomControls = false
                settings.displayZoomControls = false
                isVerticalScrollBarEnabled = false
                isHorizontalScrollBarEnabled = false
                setBackgroundColor(android.graphics.Color.TRANSPARENT)
                webChromeClient = object : WebChromeClient() {
                    override fun onConsoleMessage(message: ConsoleMessage): Boolean {
                        Log.d("BeyondEarthCanvas", "${message.message()} -- line ${message.lineNumber()} (${message.sourceId()})")
                        return true
                    }
                }
                webViewClient = object : WebViewClient() {
                    override fun onPageFinished(view: WebView, url: String?) {
                        view.evaluateJavascript(
                            "window.PadippuPalVisual ? (window.PadippuPalVisual.setStep($safeStep, ${JSONObject.quote(subtype)}), JSON.stringify(window.__padippuCanvasDiagnostics || {bridgeReady:false})) : JSON.stringify({bridgeReady:false,readyState:document.readyState})"
                        ) { result ->
                            Log.d("BeyondEarthCanvas", "pageFinished url=$url step=$safeStep subtype=$subtype diagnostics=$result")
                        }
                    }
                }
                webViewState.value = this
                loadUrl("file:///android_asset/beyond-earth/index.html")
            }
        },
        update = { view ->
            view.evaluateJavascript(
                "window.PadippuPalVisual ? (window.PadippuPalVisual.setStep($safeStep, ${JSONObject.quote(subtype)}), JSON.stringify(window.__padippuCanvasDiagnostics || {bridgeReady:false})) : JSON.stringify({bridgeReady:false,readyState:document.readyState})"
            ) { result ->
                Log.d("BeyondEarthCanvas", "update step=$safeStep subtype=$subtype diagnostics=$result")
            }
        }
    )

    DisposableEffect(Unit) {
        onDispose {
            webViewState.value?.apply {
                stopLoading()
                loadUrl("about:blank")
                destroy()
            }
            webViewState.value = null
        }
    }
}
