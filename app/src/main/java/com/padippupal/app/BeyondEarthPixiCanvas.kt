package com.padippupal.app

import android.annotation.SuppressLint
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
        modifier = modifier.height(if (compact) 230.dp else 310.dp),
        factory = { context ->
            WebView(context).apply {
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
                webViewClient = object : WebViewClient() {
                    override fun onPageFinished(view: WebView, url: String?) {
                        view.evaluateJavascript(
                            "window.PadippuPalVisual && window.PadippuPalVisual.setStep($safeStep, ${JSONObject.quote(subtype)})",
                            null
                        )
                    }
                }
                webViewState.value = this
                loadUrl("file:///android_asset/beyond-earth/index.html")
            }
        },
        update = { view ->
            view.evaluateJavascript(
                "window.PadippuPalVisual && window.PadippuPalVisual.setStep($safeStep)",
                null
            )
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
