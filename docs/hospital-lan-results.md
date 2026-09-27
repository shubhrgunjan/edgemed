# Hospital LAN demo verification

Date: 28 September 2026. All records used for this work were synthetic. Implementation and live rehearsal used an isolated, encrypted verification runtime with its own Keychain namespace and port offset; the existing local vault was not used for mutation tests.

The backend suite passed **50 tests**. New tests generated a private-IP TLS certificate, rejected public/loopback IPs and changed SANs, and exercised four staff accounts against a real SQLCipher store and Qdrant Edge retrieval. They verified workspace listing/search/detail isolation, personal record isolation, role-restricted deletion/sync, CSRF/Host/Origin rejection and disabled-account login rejection. Ruff and the TypeScript/Vite production build passed.

Four Playwright browser tests passed against the live HTTPS server on the Mac's private IP, including two separate staff sessions at a 390-pixel phone viewport. Existing capture/search/inspection/delete, keyboard focus, and stale-response-after-sign-out checks also passed. The test browser temporarily ignored trust errors for the newly generated demo CA; this does **not** establish that a physical phone has installed and trusts the CA.

The CLI successfully started Edge A on the private-IP HTTPS endpoint while Edge B, the gateway and Qdrant remained loopback bound. A separate `httpx` client verified the certificate chain and IP hostname with the generated CA, reached `/api/health`, and received 401 on an unauthenticated records request. Three staff accounts were provisioned through the CLI. Disabling one account stopped services; after restart its login returned 401 and another staff member still logged in. The test credential file was removed and the isolated vault was unmounted afterward.

A second physical client device, OS/browser CA installation, firewall policy, 30-minute internet outage rehearsal, long soak, power-loss recovery, and hospital identity-provider integration have not been tested. A browser needs LAN access to the Mac; this is not an on-phone backend. The prototype remains synthetic-data-only and has no clinical deployment approval.
