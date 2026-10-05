Index: AGENTS.md
===================================================================
diff --git a/AGENTS.md b/AGENTS.md
new file mode 100644
--- /dev/null	(revision 338398f9413b0709c2e17476f794aef7be5bab62)
+++ b/AGENTS.md	(revision 338398f9413b0709c2e17476f794aef7be5bab62)
@@ -0,0 +1,26 @@
+## Task execution discipline
+
+When asked to implement an existing TODO, implementation plan, specification, or requirements document:
+
+- Treat the entire requested item as the task, not merely the next obvious step.
+- Read the complete implementation plan and acceptance requirements before editing.
+- Maintain a checklist of all required steps and acceptance criteria.
+- Continue executing tools, editing files, and running verification until every checklist item is either complete or genuinely blocked.
+- Do not stop after completing an intermediate file, function, test, or milestone.
+- Do not ask whether to continue when the next step is already implied by the implementation plan.
+- After each substantial step, re-read the checklist and continue with the next incomplete item.
+- Before finishing, compare the implementation against every stated requirement and acceptance criterion.
+- Run the relevant tests, linting, type checking, or other verification available to the project.
+- Only end the task when:
+  1. all requested work is complete and verified;
+  2. a required decision is genuinely ambiguous and cannot be inferred safely; or
+  3. an external dependency, permission, credential, or unrecoverable error blocks further progress.
+
+At the end of every implementation task, report:
+
+- Completed: what was implemented.
+- Verification: commands/tests run and their results.
+- Remaining: anything not completed, or explicitly "None".
+- Blockers: any blockers, or explicitly "None".
+
+If work remains, do not present the task as complete.
\ No newline at end of file
