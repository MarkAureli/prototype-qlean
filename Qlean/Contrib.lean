/-!
# Qlean.Contrib

Aggregator for contributed (non-core) results. Each contribution adds its module
here with `import Qlean.Contrib.<Area>.<Name>`. Contrib may depend on `Qlean.Core`;
core never depends on Contrib. Contributed declarations live under the
`Qlean.Contrib.*` namespace so their non-canonical status is visible.
-/
