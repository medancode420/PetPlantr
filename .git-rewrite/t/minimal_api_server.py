diff --git a/minimal_api_server.py b/minimal_api_server.py
--- a/minimal_api_server.py
+++ b/minimal_api_server.py
@@ -408,14 +408,22 @@
 app.add_middleware(
     CORSMiddleware,
     allow_origins=cors_origins,
     allow_credentials=True,
     allow_methods=["GET", "POST", "OPTIONS"],
     allow_headers=["*"],
 )
 
-# Static mounts (safe defaults)
-MODEL_DIR = Path(os.getenv("PETPLANTR_MODEL_DIR", "frontend/public/models")).resolve()
-MODEL_DIR.mkdir(parents=True, exist_ok=True)
-app.mount("/models", app=FileResponse if False else None)  # noop placeholder for tests
-STATIC_DIR = Path("static").resolve()
-STATIC_DIR.mkdir(exist_ok=True)
-# (No static mount via StaticFiles here to avoid import issues if Starlette optional extras missing)
+# Static mounts (guarded)
+MODEL_DIR = Path(os.getenv("PETPLANTR_MODEL_DIR", "frontend/public/models")).resolve()
+STATIC_DIR = Path("static").resolve()
+try:
+    from fastapi.staticfiles import StaticFiles
+    MODEL_DIR.mkdir(parents=True, exist_ok=True)
+    STATIC_DIR.mkdir(parents=True, exist_ok=True)
+    app.mount("/models", StaticFiles(directory=str(MODEL_DIR), html=True), name="models")
+    app.mount("/static", StaticFiles(directory=str(STATIC_DIR), html=False), name="static")
+except Exception as e:
+    log.info("Static mounts unavailable; skipping /models and /static: %s", e)
 
@@ -1004,6 +1012,22 @@
 if PROMETHEUS_AVAILABLE:
     @app.get("/metrics")
     async def metrics():
         if METRICS_REGISTRY is None:
             raise HTTPException(status_code=500, detail="Metrics registry not available")
         return JSONResponse(content=generate_latest(METRICS_REGISTRY).decode("utf-8"), media_type=CONTENT_TYPE_LATEST)
 
@@ -1012,9 +1036,25 @@
 # Import-time convenience: pre-create ops_sync placeholder when ops endpoints enabled
 # (lets tests find app.state.ops_sync without waiting for lifespan)
 # --------------------------------------------------------------------------------------
 
 try:
     if OpsConfigSync is not None and _ops_feature_enabled():
         if not hasattr(app.state, "ops_sync") or getattr(app.state, "ops_sync", None) is None:
             app.state.ops_sync = OpsConfigSync(app)
 except Exception:
     pass
+
+# Ensure a basic hedger exists at import time too (some tests don't run lifespan)
+try:
+    if not hasattr(app.state, "hedger") or getattr(app.state, "hedger", None) is None:
+        app.state.hedger = _HedgerFacade(core_settings or {})
+except Exception:
+    pass
+
+# Allow `python minimal_api_server.py` to run directly
+if __name__ == "__main__":
+    try:
+        import uvicorn
+    except Exception as e:
+        raise SystemExit(f"uvicorn is required to run this file directly: {e}")
+    uvicorn.run("minimal_api_server:app", host="127.0.0.1", port=8000, reload=True)
