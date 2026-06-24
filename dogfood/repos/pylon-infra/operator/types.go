package main

import (
	"context"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
)

// Pylon is the custom resource the operator reconciles. One Pylon
// tracks one workload's desired image and rollout progress.
type Pylon struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   PylonSpec   `json:"spec,omitempty"`
	Status PylonStatus `json:"status,omitempty"`
}

type PylonSpec struct {
	// Image is the desired container image (registry/repo:tag).
	Image string `json:"image"`
	// SLO is the gate every rollout step must clear, e.g.
	// "availability>=99.9,p99<300ms".
	SLO string `json:"slo"`
}

type PylonStatus struct {
	Image         string `json:"image,omitempty"`
	LastGoodImage string `json:"lastGoodImage,omitempty"`
	Percent       int    `json:"percent,omitempty"`
}

// DeepCopyObject satisfies runtime.Object (normally codegen'd).
func (p *Pylon) DeepCopyObject() runtime.Object {
	out := *p
	return &out
}

// prometheusSLO is the production SLOChecker, backed by Prometheus.
type prometheusSLO struct{}

func (prometheusSLO) Healthy(ctx context.Context, name string) (bool, error) {
	// Real impl queries Prometheus for availability + p99 latency and
	// compares against the workload's SLO string. Stubbed here.
	return true, nil
}
