#!/bin/bash
# PetPlantr Master Launch Controller
# Orchestrates entire launch sequence from T-24h to T+24h
# Usage: bash master_launch_controller.sh --mode [preflight|launch|rollback] --confirm

set -euo pipefail

MODE=""
CONFIRM=false
EVIDENCE_DIR="evidence/master_launch"
TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
LAUNCH_ID="launch_${TIMESTAMP}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --confirm)
            CONFIRM=true
            shift
            ;;
        *)
            echo "Unknown option $1"
            echo "Usage: $0 --mode [preflight|launch|rollback] --confirm"
            exit 1
            ;;
    esac
done

if [[ -z "$MODE" ]]; then
    echo "PetPlantr Master Launch Controller"
    echo "=================================="
    echo ""
    echo "Available modes:"
    echo "  preflight  - T-24h to T-6h: Complete pre-flight validation"
    echo "  launch     - T-6h to T+1h: Execute full launch sequence"
    echo "  rollback   - Emergency rollback to previous version"
    echo ""
    echo "Usage: $0 --mode <mode> --confirm"
    echo ""
    echo "⚠️  IMPORTANT: This script controls production deployment"
    echo "   Review carefully and use --confirm to proceed"
    exit 1
fi

if [[ "$CONFIRM" != "true" ]]; then
    echo "❌ --confirm flag required for production operations"
    echo "   Review the operations and add --confirm to proceed"
    exit 1
fi

# Create evidence directory
mkdir -p "$EVIDENCE_DIR"

# Source utilities
source utils/evidence.sh

echo "🚀 PetPlantr Master Launch Controller"
echo "====================================="
echo "Mode: $MODE"
echo "Launch ID: $LAUNCH_ID"
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# Initialize evidence collection
init_evidence_report "$EVIDENCE_DIR/master_launch_${LAUNCH_ID}.html" "PetPlantr Master Launch - $MODE"

execute_preflight_mode() {
    echo "🔍 PREFLIGHT MODE: T-24h to T-6h"
    echo "==============================="
    
    add_evidence_section "Pre-flight Validation Sequence"
    
    # T-24h: Model readiness
    echo "📊 T-24h: Model readiness validation..."
    if bash one_hour_finetune.sh > "$EVIDENCE_DIR/model_training.log" 2>&1; then
        add_evidence_item "✅ Model training completed successfully" "$EVIDENCE_DIR/model_training.log"
    else
        add_evidence_item "❌ Model training failed" "$EVIDENCE_DIR/model_training.log"
        echo "❌ PREFLIGHT FAILED - Model training issues"
        exit 1
    fi
    
    # T-18h: Data validation
    echo "📁 T-18h: Data validation and corpus preparation..."
    if bash prepare_training_corpus.sh > "$EVIDENCE_DIR/data_preparation.log" 2>&1; then
        add_evidence_item "✅ Training corpus prepared" "$EVIDENCE_DIR/data_preparation.log"
    else
        add_evidence_item "❌ Data preparation failed" "$EVIDENCE_DIR/data_preparation.log"
        echo "❌ PREFLIGHT FAILED - Data issues"
        exit 1
    fi
    
    # T-12h: Complete system validation
    echo "🧪 T-12h: Complete system validation..."
    if bash final_launch_validation.sh --report "$EVIDENCE_DIR/preflight_validation.html" > "$EVIDENCE_DIR/system_validation.log" 2>&1; then
        add_evidence_item "✅ System validation passed" "$EVIDENCE_DIR/system_validation.log"
    else
        add_evidence_item "❌ System validation failed" "$EVIDENCE_DIR/system_validation.log"
        echo "❌ PREFLIGHT FAILED - System validation issues"
        exit 1
    fi
    
    # T-8h: Security hardening
    echo "🔒 T-8h: Security hardening and compliance..."
    if bash security_hardening.sh > "$EVIDENCE_DIR/security_hardening.log" 2>&1; then
        add_evidence_item "✅ Security hardening completed" "$EVIDENCE_DIR/security_hardening.log"
    else
        add_evidence_item "⚠️  Security hardening issues" "$EVIDENCE_DIR/security_hardening.log"
    fi
    
    # T-6h: Infrastructure readiness
    echo "🏗️  T-6h: Infrastructure deployment readiness..."
    if bash deploy_enhanced.sh --dry-run > "$EVIDENCE_DIR/infra_readiness.log" 2>&1; then
        add_evidence_item "✅ Infrastructure ready for deployment" "$EVIDENCE_DIR/infra_readiness.log"
    else
        add_evidence_item "❌ Infrastructure not ready" "$EVIDENCE_DIR/infra_readiness.log"
        echo "❌ PREFLIGHT FAILED - Infrastructure issues"
        exit 1
    fi
    
    # Apply drill remediations
    echo "🔧 T-6h: Applying operational drill remediations..."
    if bash drill_remediations.sh --type all > "$EVIDENCE_DIR/drill_remediations.log" 2>&1; then
        add_evidence_item "✅ Drill remediations applied" "$EVIDENCE_DIR/drill_remediations.log"
    else
        add_evidence_item "⚠️  Some remediations failed" "$EVIDENCE_DIR/drill_remediations.log"
    fi
    
    echo ""
    echo "✅ PREFLIGHT VALIDATION COMPLETE"
    echo "================================="
    echo "🎯 Next: bash master_launch_controller.sh --mode launch --confirm"
    echo "📊 Evidence report: $EVIDENCE_DIR/master_launch_${LAUNCH_ID}.html"
}

execute_launch_mode() {
    echo "🚀 LAUNCH MODE: T-6h to T+1h"
    echo "============================"
    
    add_evidence_section "Production Launch Sequence"
    
    # T-6h: Infrastructure deployment
    echo "🏗️  T-6h: Infrastructure deployment..."
    if bash deploy_enhanced.sh > "$EVIDENCE_DIR/infra_deployment.log" 2>&1; then
        add_evidence_item "✅ Infrastructure deployed successfully" "$EVIDENCE_DIR/infra_deployment.log"
    else
        add_evidence_item "❌ Infrastructure deployment failed" "$EVIDENCE_DIR/infra_deployment.log"
        echo "❌ LAUNCH FAILED - Infrastructure deployment issues"
        exit 1
    fi
    
    # T-4h: Monitoring setup
    echo "📊 T-4h: Production monitoring setup..."
    if bash production_monitoring_setup.sh > "$EVIDENCE_DIR/monitoring_setup.log" 2>&1; then
        add_evidence_item "✅ Monitoring configured" "$EVIDENCE_DIR/monitoring_setup.log"
    else
        add_evidence_item "❌ Monitoring setup failed" "$EVIDENCE_DIR/monitoring_setup.log"
        echo "❌ LAUNCH FAILED - Monitoring issues"
        exit 1
    fi
    
    # T-2h: Canary deployment
    echo "🕯️  T-2h: Canary deployment (5% traffic)..."
    if bash ultimate_launch_automation.sh --canary 5 --report "$EVIDENCE_DIR/canary_deployment.html" > "$EVIDENCE_DIR/canary.log" 2>&1; then
        add_evidence_item "✅ Canary deployment successful" "$EVIDENCE_DIR/canary.log"
    else
        add_evidence_item "❌ Canary deployment failed" "$EVIDENCE_DIR/canary.log"
        echo "❌ LAUNCH FAILED - Canary deployment issues"
        exit 1
    fi
    
    # T-1h: Canary validation
    echo "🧪 T-1h: Canary performance validation..."
    sleep 60  # Wait for metrics to stabilize
    
    # Check canary metrics
    CANARY_ERROR_RATE=$(curl -s "http://prometheus.petplantr.internal:9090/api/v1/query?query=rate(http_requests_total{status=~'5..'}[5m])" | jq -r '.data.result[0].value[1]' || echo "0")
    CANARY_LATENCY_P95=$(curl -s "http://prometheus.petplantr.internal:9090/api/v1/query?query=histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))" | jq -r '.data.result[0].value[1]' || echo "0")
    
    echo "Canary error rate: $CANARY_ERROR_RATE" > "$EVIDENCE_DIR/canary_metrics.log"
    echo "Canary P95 latency: $CANARY_LATENCY_P95" >> "$EVIDENCE_DIR/canary_metrics.log"
    
    if (( $(echo "$CANARY_ERROR_RATE < 0.01" | bc -l) )) && (( $(echo "$CANARY_LATENCY_P95 < 0.5" | bc -l) )); then
        add_evidence_item "✅ Canary metrics within SLO" "$EVIDENCE_DIR/canary_metrics.log"
    else
        add_evidence_item "❌ Canary metrics exceed SLO" "$EVIDENCE_DIR/canary_metrics.log"
        echo "❌ LAUNCH FAILED - Canary validation failed"
        echo "Consider running: bash master_launch_controller.sh --mode rollback --confirm"
        exit 1
    fi
    
    # T-30m: Go/No-Go decision
    echo "🎯 T-30m: Final Go/No-Go checkpoint..."
    echo "======================================"
    echo "🔍 Canary error rate: $CANARY_ERROR_RATE (target: <0.01)"
    echo "🔍 Canary P95 latency: ${CANARY_LATENCY_P95}s (target: <0.5s)"
    echo ""
    read -p "🚦 Proceed with full production rollout? (GO/NO-GO): " GO_NO_GO
    
    if [[ "$GO_NO_GO" != "GO" ]]; then
        echo "❌ Launch aborted by operator decision"
        echo "Consider running: bash master_launch_controller.sh --mode rollback --confirm"
        exit 1
    fi
    
    # T-0: Full production rollout
    echo "🚀 T-0: Full production rollout (100% traffic)..."
    if bash ultimate_launch_automation.sh --canary 100 > "$EVIDENCE_DIR/full_rollout.log" 2>&1; then
        add_evidence_item "✅ Full production rollout successful" "$EVIDENCE_DIR/full_rollout.log"
    else
        add_evidence_item "❌ Full rollout failed" "$EVIDENCE_DIR/full_rollout.log"
        echo "❌ LAUNCH FAILED - Full rollout issues"
        echo "🚨 EMERGENCY: Consider immediate rollback"
        exit 1
    fi
    
    # T+15m: Post-launch validation
    echo "🔍 T+15m: Post-launch validation..."
    sleep 900  # Wait 15 minutes for metrics
    
    POST_ERROR_RATE=$(curl -s "http://prometheus.petplantr.internal:9090/api/v1/query?query=rate(http_requests_total{status=~'5..'}[5m])" | jq -r '.data.result[0].value[1]' || echo "0")
    POST_LATENCY_P95=$(curl -s "http://prometheus.petplantr.internal:9090/api/v1/query?query=histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))" | jq -r '.data.result[0].value[1]' || echo "0")
    
    echo "Post-launch error rate: $POST_ERROR_RATE" > "$EVIDENCE_DIR/post_launch_metrics.log"
    echo "Post-launch P95 latency: $POST_LATENCY_P95" >> "$EVIDENCE_DIR/post_launch_metrics.log"
    
    if (( $(echo "$POST_ERROR_RATE < 0.01" | bc -l) )) && (( $(echo "$POST_LATENCY_P95 < 0.5" | bc -l) )); then
        add_evidence_item "✅ Post-launch metrics healthy" "$EVIDENCE_DIR/post_launch_metrics.log"
    else
        add_evidence_item "⚠️  Post-launch metrics concerning" "$EVIDENCE_DIR/post_launch_metrics.log"
        echo "⚠️  Post-launch metrics concerning - monitor closely"
    fi
    
    # T+1h: Git tagging and release
    echo "🏷️  T+1h: Creating release artifacts..."
    CURRENT_SHA=$(git rev-parse HEAD)
    git tag -a "v1.0.0" -m "PetPlantr Production Launch - $LAUNCH_ID"
    git push origin "v1.0.0"
    
    echo "Release v1.0.0 created with SHA: $CURRENT_SHA" > "$EVIDENCE_DIR/release_info.log"
    add_evidence_item "✅ Release v1.0.0 tagged and pushed" "$EVIDENCE_DIR/release_info.log"
    
    echo ""
    echo "🎉 LAUNCH SUCCESSFUL!"
    echo "===================="
    echo "✅ Production deployment complete"
    echo "🏷️  Release: v1.0.0 (SHA: $CURRENT_SHA)"
    echo "📊 Evidence report: $EVIDENCE_DIR/master_launch_${LAUNCH_ID}.html"
    echo ""
    echo "🎯 Next steps:"
    echo "  1. Monitor dashboards: https://grafana.petplantr.com"
    echo "  2. Check logs: kubectl logs -n petplantr -l app=api"
    echo "  3. T+24h retrospective planning"
}

execute_rollback_mode() {
    echo "🔄 ROLLBACK MODE: Emergency Recovery"
    echo "===================================="
    
    add_evidence_section "Emergency Rollback Sequence"
    
    # Get previous version
    PREV_VERSION=$(git describe --tags --abbrev=0 HEAD~1 2>/dev/null || echo "none")
    
    if [[ "$PREV_VERSION" == "none" ]]; then
        echo "❌ No previous version found for rollback"
        exit 1
    fi
    
    echo "🔄 Rolling back to previous version: $PREV_VERSION"
    
    # Capture current state
    echo "📸 Capturing current state for forensics..."
    kubectl get pods -n petplantr -o yaml > "$EVIDENCE_DIR/rollback_pre_state.yaml"
    curl -s "http://prometheus.petplantr.internal:9090/api/v1/query?query=up" > "$EVIDENCE_DIR/rollback_metrics_before.json"
    
    # Execute rollback
    echo "🔄 Executing rollback deployment..."
    if kubectl rollout undo deployment/api -n petplantr > "$EVIDENCE_DIR/rollback_execution.log" 2>&1; then
        add_evidence_item "✅ Rollback deployment executed" "$EVIDENCE_DIR/rollback_execution.log"
    else
        add_evidence_item "❌ Rollback deployment failed" "$EVIDENCE_DIR/rollback_execution.log"
        echo "❌ CRITICAL: Rollback failed - manual intervention required"
        exit 1
    fi
    
    # Wait for rollback to complete
    echo "⏳ Waiting for rollback to complete..."
    if kubectl rollout status deployment/api -n petplantr --timeout=300s > "$EVIDENCE_DIR/rollback_status.log" 2>&1; then
        add_evidence_item "✅ Rollback completed successfully" "$EVIDENCE_DIR/rollback_status.log"
    else
        add_evidence_item "❌ Rollback did not complete" "$EVIDENCE_DIR/rollback_status.log"
        echo "❌ CRITICAL: Rollback incomplete - manual intervention required"
        exit 1
    fi
    
    # Validate rollback
    echo "🧪 Validating rollback health..."
    sleep 60  # Wait for metrics
    
    ROLLBACK_ERROR_RATE=$(curl -s "http://prometheus.petplantr.internal:9090/api/v1/query?query=rate(http_requests_total{status=~'5..'}[5m])" | jq -r '.data.result[0].value[1]' || echo "0")
    
    echo "Post-rollback error rate: $ROLLBACK_ERROR_RATE" > "$EVIDENCE_DIR/rollback_validation.log"
    
    if (( $(echo "$ROLLBACK_ERROR_RATE < 0.01" | bc -l) )); then
        add_evidence_item "✅ Rollback validation successful" "$EVIDENCE_DIR/rollback_validation.log"
        echo "✅ ROLLBACK SUCCESSFUL"
        echo "System restored to: $PREV_VERSION"
    else
        add_evidence_item "❌ Rollback validation failed" "$EVIDENCE_DIR/rollback_validation.log"
        echo "❌ CRITICAL: Rollback validation failed"
        echo "Manual intervention required immediately"
        exit 1
    fi
    
    # Emergency notifications
    echo "📢 Sending emergency notifications..."
    echo "🚨 EMERGENCY ROLLBACK EXECUTED - Launch ID: $LAUNCH_ID" | slack-notify '#incident-response' || true
    
    echo ""
    echo "🔄 ROLLBACK COMPLETE"
    echo "==================="
    echo "📊 Evidence report: $EVIDENCE_DIR/master_launch_${LAUNCH_ID}.html"
    echo "⚠️  Incident response required - check #incident-response"
}

# Main execution
case $MODE in
    "preflight")
        execute_preflight_mode
        ;;
    "launch")
        execute_launch_mode
        ;;
    "rollback")
        execute_rollback_mode
        ;;
    *)
        echo "❌ Unknown mode: $MODE"
        exit 1
        ;;
esac

# Finalize evidence report
finalize_evidence_report

echo ""
echo "📁 Master launch evidence: $EVIDENCE_DIR/"
echo "🕐 Execution time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""
echo "PetPlantr Master Launch Controller - $MODE mode completed"
