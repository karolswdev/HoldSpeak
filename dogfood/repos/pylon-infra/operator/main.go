// Command operator runs the Pylon controller: it reconciles Pylon
// custom resources by driving a progressive rollout (canary -> 10% ->
// 100%) and gating each step on the workload's SLO.
//
// INVARIANT: the operator is the ONLY actor that mutates prod workload
// state. No manual kubectl in prod (.hs/memory.md).
package main

import (
	"context"
	"fmt"
	"time"

	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/log"
)

// rolloutSteps is the fixed progression every prod rollout follows.
var rolloutSteps = []int{1, 10, 100} // canary, 10%, 100% (percent)

// PylonReconciler reconciles a Pylon object toward its desired image,
// advancing one rollout step per reconcile once the SLO gate passes.
type PylonReconciler struct {
	client.Client
	SLO SLOChecker
}

// SLOChecker reports whether the workload currently meets its SLO.
// Backed by Prometheus in prod; faked in tests.
type SLOChecker interface {
	Healthy(ctx context.Context, name string) (bool, error)
}

func (r *PylonReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	l := log.FromContext(ctx).WithValues("pylon", req.NamespacedName)

	var p Pylon
	if err := r.Get(ctx, req.NamespacedName, &p); err != nil {
		return ctrl.Result{}, client.IgnoreNotFound(err)
	}

	// Already at the desired image and fully rolled out: nothing to do.
	if p.Status.Image == p.Spec.Image && p.Status.Percent == 100 {
		return ctrl.Result{}, nil
	}

	// New image requested: restart the progression at the canary step.
	if p.Status.Image != p.Spec.Image {
		l.Info("new image, starting canary", "image", p.Spec.Image)
		p.Status.Image = p.Spec.Image
		p.Status.Percent = rolloutSteps[0]
		return ctrl.Result{}, r.advance(ctx, &p)
	}

	// Gate the next step on the SLO. A breach halts and rolls back.
	ok, err := r.SLO.Healthy(ctx, p.Name)
	if err != nil {
		return ctrl.Result{RequeueAfter: 30 * time.Second}, err
	}
	if !ok {
		l.Info("SLO breach during rollout, rolling back", "percent", p.Status.Percent)
		return ctrl.Result{}, r.rollback(ctx, &p)
	}

	next, done := nextStep(p.Status.Percent)
	p.Status.Percent = next
	if done {
		l.Info("rollout complete", "image", p.Spec.Image)
	}
	// Soak between steps before re-evaluating the SLO.
	return ctrl.Result{RequeueAfter: 2 * time.Minute}, r.advance(ctx, &p)
}

// nextStep returns the next rollout percentage and whether it's the last.
func nextStep(current int) (int, bool) {
	for i, s := range rolloutSteps {
		if s == current {
			if i+1 < len(rolloutSteps) {
				return rolloutSteps[i+1], false
			}
			return 100, true
		}
	}
	return rolloutSteps[0], false
}

func (r *PylonReconciler) advance(ctx context.Context, p *Pylon) error {
	// In a real cluster this patches the Deployment's replica split.
	return r.Status().Update(ctx, p)
}

func (r *PylonReconciler) rollback(ctx context.Context, p *Pylon) error {
	p.Status.Image = p.Status.LastGoodImage
	p.Status.Percent = 100
	return r.Status().Update(ctx, p)
}

func main() {
	mgr, err := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{})
	if err != nil {
		panic(fmt.Errorf("create manager: %w", err))
	}
	if err := ctrl.NewControllerManagedBy(mgr).
		For(&Pylon{}).
		Complete(&PylonReconciler{Client: mgr.GetClient(), SLO: prometheusSLO{}}); err != nil {
		panic(fmt.Errorf("create controller: %w", err))
	}
	if err := mgr.Start(ctrl.SetupSignalHandler()); err != nil {
		panic(fmt.Errorf("start manager: %w", err))
	}
}
