{{- define "agent-factory.name" -}}agent-factory{{- end }}
{{- define "agent-factory.fullname" -}}{{ .Release.Name }}-agent-factory{{- end }}
{{- define "agent-factory.labels" -}}
app.kubernetes.io/name: {{ include "agent-factory.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
