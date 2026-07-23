react-dom_client.js?v=7b28abce:14336 Download the React DevTools for a better development experience: https://react.dev/link/react-devtools
Dashboard.tsx:78 Uncaught TypeError: Cannot read properties of undefined (reading 'charAt')
    at Dashboard.tsx:78:29
    at Array.map (<anonymous>)
    at Dashboard (Dashboard.tsx:71:42)
    at Object.react_stack_bottom_frame (react-dom_client.js?v=7b28abce:12866:12)
    at renderWithHooks (react-dom_client.js?v=7b28abce:4213:19)
    at updateFunctionComponent (react-dom_client.js?v=7b28abce:5569:16)
    at beginWork (react-dom_client.js?v=7b28abce:6140:20)
    at runWithFiberInDEV (react-dom_client.js?v=7b28abce:851:66)
    at performUnitOfWork (react-dom_client.js?v=7b28abce:8429:92)
    at workLoopSync (react-dom_client.js?v=7b28abce:8325:37)
(anonymous) @ Dashboard.tsx:78
(anonymous) @ Dashboard.tsx:71
react_stack_bottom_frame @ react-dom_client.js?v=7b28abce:12866
renderWithHooks @ react-dom_client.js?v=7b28abce:4213
updateFunctionComponent @ react-dom_client.js?v=7b28abce:5569
beginWork @ react-dom_client.js?v=7b28abce:6140
runWithFiberInDEV @ react-dom_client.js?v=7b28abce:851
performUnitOfWork @ react-dom_client.js?v=7b28abce:8429
workLoopSync @ react-dom_client.js?v=7b28abce:8325
renderRootSync @ react-dom_client.js?v=7b28abce:8309
performWorkOnRoot @ react-dom_client.js?v=7b28abce:7994
performWorkOnRootViaSchedulerTask @ react-dom_client.js?v=7b28abce:9059
performWorkUntilDeadline @ react-dom_client.js?v=7b28abce:36
<Dashboard>
exports.jsxDEV @ react_jsx-dev-runtime.js?v=7b28abce:193
App @ App.tsx:25
react_stack_bottom_frame @ react-dom_client.js?v=7b28abce:12866
renderWithHooksAgain @ react-dom_client.js?v=7b28abce:4268
renderWithHooks @ react-dom_client.js?v=7b28abce:4219
updateFunctionComponent @ react-dom_client.js?v=7b28abce:5569
beginWork @ react-dom_client.js?v=7b28abce:6140
runWithFiberInDEV @ react-dom_client.js?v=7b28abce:851
performUnitOfWork @ react-dom_client.js?v=7b28abce:8429
workLoopSync @ react-dom_client.js?v=7b28abce:8325
renderRootSync @ react-dom_client.js?v=7b28abce:8309
performWorkOnRoot @ react-dom_client.js?v=7b28abce:7957
performWorkOnRootViaSchedulerTask @ react-dom_client.js?v=7b28abce:9059
performWorkUntilDeadline @ react-dom_client.js?v=7b28abce:36
<App>
exports.jsxDEV @ react_jsx-dev-runtime.js?v=7b28abce:193
(anonymous) @ main.tsx:8
App.tsx:25 An error occurred in the <Dashboard> component.

Consider adding an error boundary to your tree to customize error handling behavior.
Visit https://react.dev/link/error-boundaries to learn more about error boundaries.

defaultOnUncaughtError @ react-dom_client.js?v=7b28abce:5258
logUncaughtError @ react-dom_client.js?v=7b28abce:5287
runWithFiberInDEV @ react-dom_client.js?v=7b28abce:851
lane.callback @ react-dom_client.js?v=7b28abce:5315
callCallback @ react-dom_client.js?v=7b28abce:4095
commitCallbacks @ react-dom_client.js?v=7b28abce:4103
runWithFiberInDEV @ react-dom_client.js?v=7b28abce:851
commitLayoutEffectOnFiber @ react-dom_client.js?v=7b28abce:6986
flushLayoutEffects @ react-dom_client.js?v=7b28abce:8671
commitRoot @ react-dom_client.js?v=7b28abce:8584
commitRootWhenReady @ react-dom_client.js?v=7b28abce:8079
performWorkOnRoot @ react-dom_client.js?v=7b28abce:8051
performWorkOnRootViaSchedulerTask @ react-dom_client.js?v=7b28abce:9059
performWorkUntilDeadline @ react-dom_client.js?v=7b28abce:36
<Dashboard>
exports.jsxDEV @ react_jsx-dev-runtime.js?v=7b28abce:193
App @ App.tsx:25
react_stack_bottom_frame @ react-dom_client.js?v=7b28abce:12866
renderWithHooksAgain @ react-dom_client.js?v=7b28abce:4268
renderWithHooks @ react-dom_client.js?v=7b28abce:4219
updateFunctionComponent @ react-dom_client.js?v=7b28abce:5569
beginWork @ react-dom_client.js?v=7b28abce:6140
runWithFiberInDEV @ react-dom_client.js?v=7b28abce:851
performUnitOfWork @ react-dom_client.js?v=7b28abce:8429
workLoopSync @ react-dom_client.js?v=7b28abce:8325
renderRootSync @ react-dom_client.js?v=7b28abce:8309
performWorkOnRoot @ react-dom_client.js?v=7b28abce:7957
performWorkOnRootViaSchedulerTask @ react-dom_client.js?v=7b28abce:9059
performWorkUntilDeadline @ react-dom_client.js?v=7b28abce:36
<App>
exports.jsxDEV @ react_jsx-dev-runtime.js?v=7b28abce:193
(anonymous) @ main.tsx:8
