# Plugin Selection UX

## Scope

This flow covers domain selection for:

- new documents
- empty or bootstrap-only documents
- legacy documents without explicit plugin binding
- already bound documents

## New Or Switchable Document

Use the `Select Domain` command before creating a project.

The command:

1. lists available domain plugins
2. activates the selected domain
3. keeps the document switchable until meaningful project content exists

The active plugin and document state are shown in the workbench context summary.

## Bound Document

Once a document contains meaningful project content, the domain is considered bound.

At that point:

- the active plugin is restored from document metadata
- manual domain switching is blocked
- the UI shows a clear message explaining that a new document is required for another domain

## Legacy Document

If plugin metadata is missing, the lifecycle tries to infer the domain from persisted template, variant, or component references.

If inference succeeds, the corresponding domain is activated automatically.

## Visibility

The workbench header context summary now includes:

- active plugin id
- whether the document is `domain bound`, `domain switchable`, `legacy unbound`, or `document empty`

Status messages also explain whether the document can still switch domains.
