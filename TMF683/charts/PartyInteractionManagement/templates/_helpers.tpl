{{/*
Render eventNotification entries in a CRD-compatible format.
Accept either a list of strings or a list of maps; strings are promoted to {name: ...}.
*/}}
{{- define "partyinteractionmanagement.renderEventList" -}}
{{- $state := dict "events" (list) -}}
{{- range $event := (. | default (list)) -}}
{{- if kindIs "string" $event -}}
{{- $_ := set $state "events" (append $state.events (dict "name" $event)) -}}
{{- else -}}
{{- $_ := set $state "events" (append $state.events $event) -}}
{{- end -}}
{{- end -}}
{{- if $state.events -}}
{{ toYaml $state.events | trim }}
{{- else -}}
[]
{{- end }}
{{- end }}
