/** Synthetic contract fixtures only. Nothing in this file is a publication plan. */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
const adjacentRuntime=new URL('./regions.mjs',import.meta.url);
const runtime=await import(fs.existsSync(adjacentRuntime)?adjacentRuntime.href:new URL('../src/lib/regions.mjs',import.meta.url).href);
// Embedded original adapter permits the identical legacy regression suite in an assembled source.
const baselineBytes=Buffer.from('LyoqIEV4cGxpY2l0IGRhdGEgYWRhcHRlci4gR2VvZ3JhcGhpYyBpbnZlbnRvcnkgaXMgbm90IHBlcm1pc3Npb24gdG8gcHVibGlzaC4gKi8KY29uc3QgZmFpbCA9IHJlYXNvbiA9PiB7IHRocm93IG5ldyBFcnJvcihgUmVnaW9uYWwgc2VydmljZTogJHtyZWFzb259YCk7IH07CmNvbnN0IHVuaXF1ZT0oaXRlbXMsa2V5KT0+e2NvbnN0IHZhbHVlcz1pdGVtcy5tYXAoeD0+eFtrZXldKTtpZih2YWx1ZXMuc29tZSh4PT4heCl8fG5ldyBTZXQodmFsdWVzKS5zaXplIT09dmFsdWVzLmxlbmd0aClmYWlsKGBkdXBsaWNhdGUvbWlzc2luZyAke2tleX1gKTt9Owpjb25zdCBwYXRoU2FmZT11cmw9Pi9eXC9bYS16MC05LV0rXC9bYS16MC05LV0rXC8kLy50ZXN0KHVybCk7CmNvbnN0IG9mZmljaWFsPSh2YWx1ZSxob3N0cyk9Pnt0cnl7Y29uc3QgdT1uZXcgVVJMKHZhbHVlKTtyZXR1cm4gdS5wcm90b2NvbD09PSdodHRwczonJiYhdS51c2VybmFtZSYmIXUucGFzc3dvcmQmJmhvc3RzLmluY2x1ZGVzKHUuaG9zdG5hbWUpO31jYXRjaHtyZXR1cm4gZmFsc2U7fX07CmV4cG9ydCBjb25zdCBpc1JlZ2lvbmFsID0gcGFnZSA9PiBwYWdlLmNhdGVnb3J5PT09J3JlZ2lvbnMnfHxwYWdlLnBhZ2VUeXBlPT09J3JlZ2lvbmFsLXNlcnZpY2UnOwpleHBvcnQgZnVuY3Rpb24gdmFsaWRhdGVEZWZpbml0aW9uKGNvdmVyYWdlLHBvbGljeSkgewogaWYoY292ZXJhZ2U/LnNjaGVtYVZlcnNpb24hPT0yfHxwb2xpY3k/LnNjaGVtYVZlcnNpb24hPT0xfHxjb3ZlcmFnZS5zaXRlS2V5IT09cG9saWN5LnNpdGVLZXl8fGNvdmVyYWdlLnNjb3BlS2V5IT09cG9saWN5LnNjb3BlS2V5fHwhcG9saWN5LnNjb3BlS2V5KWZhaWwoJ3NpdGUvc2NvcGUgb3B0LWluIG1pc21hdGNoJyk7CiBpZihjb3ZlcmFnZS51bml0QmFzaXMhPT0nbGVnYWwtZG9uZy1wbHVzLWV1cC1teWVvbid8fGNvdmVyYWdlLmNvdW50SXNQYWdlUXVvdGEhPT1mYWxzZSlmYWlsKCd1bnN1cHBvcnRlZCB1bml0IGJhc2lzIG9yIHF1b3RhJyk7CiBpZighQXJyYXkuaXNBcnJheShwb2xpY3kub2ZmaWNpYWxIb3N0cyl8fCFwb2xpY3kub2ZmaWNpYWxIb3N0cy5sZW5ndGh8fCFBcnJheS5pc0FycmF5KHBvbGljeS51bml0VHlwZXMpfHwhcG9saWN5LnVuaXRUeXBlcy5sZW5ndGgpZmFpbCgnbWlzc2luZyB0cnVzdGVkIHBvbGljeScpOwogaWYoIS9eXGR7NH0tXGR7Mn0tXGR7Mn0kLy50ZXN0KGNvdmVyYWdlLnZlcmlmaWVkQXR8fCcnKXx8IWNvdmVyYWdlLnNvdXJjZUJhc2lzRGF0ZXx8IWNvdmVyYWdlLm9mZmljaWFsU291cmNlVXJscz8ubGVuZ3RoKWZhaWwoJ21pc3NpbmcgcHJvdmVuYW5jZScpOwogaWYoY292ZXJhZ2Uub2ZmaWNpYWxTb3VyY2VVcmxzLnNvbWUodXJsPT4hb2ZmaWNpYWwodXJsLHBvbGljeS5vZmZpY2lhbEhvc3RzKSkpZmFpbCgndW50cnVzdGVkIG9mZmljaWFsIHNvdXJjZScpOwogZm9yKGNvbnN0IGZpZWxkIG9mIFsnZGlzdHJpY3RzJywndW5pdHMnLCdhZG1pbmlzdHJhdGl2ZUNyb3Nzd2FsaycsJ3JlcHJlc2VudGF0aXZlcyddKWlmKCFBcnJheS5pc0FycmF5KGNvdmVyYWdlW2ZpZWxkXSkpZmFpbChgbWlzc2luZyAke2ZpZWxkfWApOwogdW5pcXVlKGNvdmVyYWdlLmRpc3RyaWN0cywna2V5Jyk7dW5pcXVlKGNvdmVyYWdlLnVuaXRzLCd1bml0S2V5Jyk7dW5pcXVlKGNvdmVyYWdlLmFkbWluaXN0cmF0aXZlQ3Jvc3N3YWxrLCdhbGlhc0tleScpOwogY29uc3QgZGlzdHJpY3RzPW5ldyBTZXQoY292ZXJhZ2UuZGlzdHJpY3RzLm1hcCh4PT54LmtleSkpO2NvbnN0IHVuaXRzPW5ldyBNYXAoY292ZXJhZ2UudW5pdHMubWFwKHg9Plt4LnVuaXRLZXkseF0pKTsKIGZvcihjb25zdCBkIG9mIGNvdmVyYWdlLmRpc3RyaWN0cylpZighL15bYS16XVthLXowLTktXSokLy50ZXN0KGQua2V5KXx8IWQubmFtZXx8IWNvdmVyYWdlLm9mZmljaWFsU291cmNlVXJscy5pbmNsdWRlcyhkLnNvdXJjZVVybCkpZmFpbCgnZGlzdHJpY3Qgc291cmNlIG1pc21hdGNoJyk7CiBmb3IoY29uc3QgdSBvZiBjb3ZlcmFnZS51bml0cylpZighdS5uYW1lfHwhcG9saWN5LnVuaXRUeXBlcy5pbmNsdWRlcyh1LnVuaXRUeXBlKXx8IXUuZGlzdHJpY3RLZXlzPy5sZW5ndGh8fG5ldyBTZXQodS5kaXN0cmljdEtleXMpLnNpemUhPT11LmRpc3RyaWN0S2V5cy5sZW5ndGh8fHUuZGlzdHJpY3RLZXlzLnNvbWUoeD0+IWRpc3RyaWN0cy5oYXMoeCkpfHwhQXJyYXkuaXNBcnJheSh1LmxlZ2FsUmkpKWZhaWwoYGludmFsaWQgdW5pdCAke3UudW5pdEtleX1gKTsKIGZvcihjb25zdCBhIG9mIGNvdmVyYWdlLmFkbWluaXN0cmF0aXZlQ3Jvc3N3YWxrKXsKICBpZighYS5uYW1lfHwhZGlzdHJpY3RzLmhhcyhhLmRpc3RyaWN0S2V5KXx8IUFycmF5LmlzQXJyYXkoYS5yZWxhdGlvbnMpKWZhaWwoJ2ludmFsaWQgYWRtaW5pc3RyYXRpdmUgYWxpYXMnKTsKICBpZighYS5yZWxhdGlvbnMubGVuZ3RoJiYhYS51bnJlc29sdmVkQ2FuZGlkYXRlTmFtZXM/Lmxlbmd0aClmYWlsKCdlbXB0eSBhbGlhcyByZXF1aXJlcyBleHBsaWNpdCB1bnJlc29sdmVkIGV2aWRlbmNlJyk7CiAgdW5pcXVlKGEucmVsYXRpb25zLCd1bml0S2V5Jyk7CiAgZm9yKGNvbnN0IHJlbCBvZiBhLnJlbGF0aW9ucylpZighdW5pdHMuaGFzKHJlbC51bml0S2V5KXx8IXVuaXRzLmdldChyZWwudW5pdEtleSkuZGlzdHJpY3RLZXlzLmluY2x1ZGVzKGEuZGlzdHJpY3RLZXkpfHwhWyd3aG9sZScsJ3BhcnRpYWwnLCduYW1lLW9ubHknLCdoaXN0b3JpY2FsJ10uaW5jbHVkZXMocmVsLnNjb3BlKSlmYWlsKGBpbnZhbGlkIGFsaWFzIHJlbGF0aW9uICR7YS5hbGlhc0tleX1gKTsKIH0KIGZvcihjb25zdCBrZXkgb2YgWydwYWdlS2V5JywndXJsJywnaW50ZW50S2V5JywncHJpbWFyeUtleXdvcmQnXSl1bmlxdWUoY292ZXJhZ2UucmVwcmVzZW50YXRpdmVzLGtleSk7CiBjb25zdCBhc3NpZ25lZD1uZXcgU2V0KCk7CiBmb3IoY29uc3QgciBvZiBjb3ZlcmFnZS5yZXByZXNlbnRhdGl2ZXMpewogIGlmKCFwYXRoU2FmZShyLnVybCl8fCFyLnByaW1hcnlLZXl3b3JkfHwhci5xdWVyeUV2aWRlbmNlfHwhci51bml0S2V5cz8ubGVuZ3RofHwhWydyZWdpb25hbCcsJ2V4aXN0aW5nJ10uaW5jbHVkZXMoci5yb3V0ZU1vZGUpfHwhWydjYW5kaWRhdGUnLCdhcHByb3ZlZCcsJ3Jlc2VydmVkJ10uaW5jbHVkZXMoci5zdGF0dXMpKWZhaWwoJ2ludmFsaWQgcmVwcmVzZW50YXRpdmUnKTsKICBpZihyLnJvdXRlTW9kZT09PSdyZWdpb25hbCcmJnIudXJsIT09YC9yZWdpb25zLyR7ci5zbHVnfS9gKWZhaWwoJ3JlZ2lvbmFsIGNhbm9uaWNhbCBtaXNtYXRjaCcpOwogIGZvcihjb25zdCBrZXkgb2Ygci51bml0S2V5cyl7aWYoIXVuaXRzLmhhcyhrZXkpfHxhc3NpZ25lZC5oYXMoa2V5KSlmYWlsKCdkdXBsaWNhdGUvdW5rbm93biBjYW5vbmljYWwgdW5pdCcpO2Fzc2lnbmVkLmFkZChrZXkpO30KIH0KIHJldHVybiBjb3ZlcmFnZTsKfQpleHBvcnQgZnVuY3Rpb24gcmVnaW9uYWxSb3dzKHBhZ2VzLGFyY2hpdGVjdHVyZSxjb3ZlcmFnZSxwb2xpY3kpIHsKIHZhbGlkYXRlRGVmaW5pdGlvbihjb3ZlcmFnZSxwb2xpY3kpOwogY29uc3Qgcm93cz1wYWdlcy5maWx0ZXIoaXNSZWdpb25hbCk7CiBpZihyb3dzLmxlbmd0aCYmYXJjaGl0ZWN0dXJlLnNpdGVLZXkhPT1jb3ZlcmFnZS5zaXRlS2V5KWZhaWwoJ2FyY2hpdGVjdHVyZSBzaXRlIG1pc21hdGNoJyk7CiBpZihyb3dzLmxlbmd0aCYmcG9saWN5LmVuYWJsZWQhPT10cnVlKWZhaWwoJ3JlZ2lvbiBzY29wZSBpcyBkaXNhYmxlZCcpOwogdW5pcXVlKHJvd3MsJ3BhZ2VLZXknKTt1bmlxdWUocm93cywndXJsJyk7CiBmb3IoY29uc3QgcCBvZiByb3dzKXsKICBjb25zdCByPWNvdmVyYWdlLnJlcHJlc2VudGF0aXZlcy5maW5kKHI9PnIucGFnZUtleT09PXAucGFnZUtleSk7CiAgY29uc3Qgbj1hcmNoaXRlY3R1cmUucGFnZXMuZmluZChuPT5uLnBhZ2VLZXk9PT1wLnBhZ2VLZXkpOwogIGlmKCFyfHxyLnN0YXR1cyE9PSdhcHByb3ZlZCd8fHIucm91dGVNb2RlIT09J3JlZ2lvbmFsJ3x8cC5jYXRlZ29yeSE9PSdyZWdpb25zJ3x8cC5wYWdlVHlwZSE9PSdyZWdpb25hbC1zZXJ2aWNlJ3x8cC5yb3V0ZVR5cGUhPT0nY2F0ZWdvcnknfHxwLnVybCE9PXIudXJsfHxwLnNsdWchPT1yLnNsdWd8fHAuc2NvcGVLZXkhPT1wb2xpY3kuc2NvcGVLZXl8fHAuc3RhdHVzIT09J2FwcHJvdmVkJ3x8cC5hcHByb3ZhbFZlcmlmaWVkIT09dHJ1ZXx8IXAuc25hcHNob3RJZHx8IXAuc25hcHNob3RIYXNoKWZhaWwoYHJvdXRlL2FwcHJvdmFsIG1pc21hdGNoICR7cC5wYWdlS2V5fWApOwogIGlmKG4/LnVybCE9PXAudXJsfHxuPy5wYWdlUm9sZSE9PSdSRUdJT05fU0VSVklDRV9MQU5ESU5HJ3x8bi5wYXJlbnRIdWIhPT0nL3JlZ2lvbnMvJ3x8bi5sb2NhbGl6YXRpb25Qb2xpY3khPT0nbG9jYWwtcmVxdWlyZWQnfHxuLmludGVudEtleSE9PXIuaW50ZW50S2V5fHxuLnNjb3BlS2V5IT09cG9saWN5LnNjb3BlS2V5KWZhaWwoYHNlbWFudGljIG1pc21hdGNoICR7cC5wYWdlS2V5fWApOwogfQogcmV0dXJuIHJvd3M7Cn0KZXhwb3J0IGZ1bmN0aW9uIGRpcmVjdG9yeUdyb3VwcyhwYWdlcyxhcmNoaXRlY3R1cmUsY292ZXJhZ2UscG9saWN5KSB7CiBjb25zdCByb3dzPXJlZ2lvbmFsUm93cyhwYWdlcyxhcmNoaXRlY3R1cmUsY292ZXJhZ2UscG9saWN5KTtpZihwb2xpY3kuZW5hYmxlZCE9PXRydWUpcmV0dXJuIFtdOwogY29uc3QgcHVibGlzaGVkPW5ldyBNYXAocm93cy5tYXAocD0+W3AucGFnZUtleSxwXSkpOwogY29uc3QgcmVwcmVzZW50YXRpdmVzPWNvdmVyYWdlLnJlcHJlc2VudGF0aXZlcy5maWx0ZXIocj0+ci5zdGF0dXM9PT0nYXBwcm92ZWQnJiZwdWJsaXNoZWQuaGFzKHIucGFnZUtleSkpOwogcmV0dXJuIGNvdmVyYWdlLmRpc3RyaWN0cy5tYXAoZD0+KHsuLi5kLGl0ZW1zOnJlcHJlc2VudGF0aXZlcy5maWx0ZXIocj0+ci51bml0S2V5cy5zb21lKGtleT0+Y292ZXJhZ2UudW5pdHMuZmluZCh1PT51LnVuaXRLZXk9PT1rZXkpLmRpc3RyaWN0S2V5cy5pbmNsdWRlcyhkLmtleSkpKS5tYXAocj0+KHtyZXByZXNlbnRhdGl2ZTpyLHBhZ2U6cHVibGlzaGVkLmdldChyLnBhZ2VLZXkpLGFsaWFzZXM6Y292ZXJhZ2UuYWRtaW5pc3RyYXRpdmVDcm9zc3dhbGsuZmlsdGVyKGE9PmEuZGlzdHJpY3RLZXk9PT1kLmtleSYmYS5yZWxhdGlvbnMuc29tZShyZWw9PnIudW5pdEtleXMuaW5jbHVkZXMocmVsLnVuaXRLZXkpKSkubWFwKGE9Pih7bmFtZTphLm5hbWUsc2NvcGU6YS5yZWxhdGlvbnMuZmluZChyZWw9PnIudW5pdEtleXMuaW5jbHVkZXMocmVsLnVuaXRLZXkpKS5zY29wZX0pKX0pKX0pKS5maWx0ZXIoZD0+ZC5pdGVtcy5sZW5ndGgpOwp9CmV4cG9ydCBmdW5jdGlvbiBhbGlhc1RhcmdldHMobmFtZSxwYWdlcyxhcmNoaXRlY3R1cmUsY292ZXJhZ2UscG9saWN5KSB7CiBjb25zdCBncm91cHM9ZGlyZWN0b3J5R3JvdXBzKHBhZ2VzLGFyY2hpdGVjdHVyZSxjb3ZlcmFnZSxwb2xpY3kpO3JldHVybiBbLi4ubmV3IFNldChncm91cHMuZmxhdE1hcChkPT5kLml0ZW1zKS5maWx0ZXIoeD0+eC5hbGlhc2VzLnNvbWUoYT0+YS5uYW1lPT09bmFtZSl8fHgucmVwcmVzZW50YXRpdmUudW5pdEtleXMuc29tZShrPT4oY292ZXJhZ2UudW5pdHMuZmluZCh1PT51LnVuaXRLZXk9PT1rKS5uYW1lPT09bmFtZXx8Y292ZXJhZ2UudW5pdHMuZmluZCh1PT51LnVuaXRLZXk9PT1rKS5sZWdhbFJpLmluY2x1ZGVzKG5hbWUpKSkpLm1hcCh4PT54LnBhZ2UudXJsKSldOwp9CmV4cG9ydCBmdW5jdGlvbiBodWJTdGF0ZShjb3VudCxzaXRlSW5kZXhhYmxlPWZhbHNlKXtpZighTnVtYmVyLmlzSW50ZWdlcihjb3VudCl8fGNvdW50PDApZmFpbCgnaW52YWxpZCBodWIgY291bnQnKTtyZXR1cm4ge2V4aXN0czpjb3VudD4wLGluZGV4YWJsZTpzaXRlSW5kZXhhYmxlJiZjb3VudD49MyxtZW51OmNvdW50Pj01LHNpdGVtYXA6c2l0ZUluZGV4YWJsZSYmY291bnQ+PTN9O30KCmV4cG9ydCBmdW5jdGlvbiB2YWxpZGF0ZVJlZ2lvbmFsUHVyY2hhc2UocGFnZSxwcm9kdWN0cyx0ZXh0PScnKSB7CiBpZighaXNSZWdpb25hbChwYWdlKSlyZXR1cm47CiBjb25zdCBtb2RlPXBhZ2UucmVnaW9uYWxQdXJjaGFzZU1vZGUsa2V5cz1wYWdlLnJlZ2lvbmFsUHJvZHVjdEtleXMsZmFtaWxpZXM9cGFnZS5yZWdpb25hbFByb2R1Y3RGYW1pbGllczsKIGlmKCFbJ2NhdGFsb2cnLCdjb25zdWx0YXRpb24tb25seSddLmluY2x1ZGVzKG1vZGUpfHwhQXJyYXkuaXNBcnJheShrZXlzKXx8IUFycmF5LmlzQXJyYXkoZmFtaWxpZXMpKWZhaWwoJ21pc3NpbmcgcHVyY2hhc2UgY29udHJhY3QnKTsKIGlmKG1vZGU9PT0nY29uc3VsdGF0aW9uLW9ubHknJiYoa2V5cy5sZW5ndGh8fGZhbWlsaWVzLmxlbmd0aCkpZmFpbCgnY29uc3VsdGF0aW9uLW9ubHkgaGFzIHByb2R1Y3QgcHJvbWlzZXMnKTsKIGlmKG1vZGU9PT0nY2F0YWxvZycmJiFrZXlzLmxlbmd0aClmYWlsKCdtaXNzaW5nIHByb2R1Y3QgbWFwcGluZycpOwogY29uc3QgbWFwcGluZz17ZnVuZXJhbF93cmVhdGg6J2Z1bmVyYWwnLGNvbmdyYXRzX3dyZWF0aDonY29uZ3JhdHMnLGZsb3dlcl9ib3VxdWV0Oidib3VxdWV0JyxmbG93ZXJfYmFza2V0OidiYXNrZXQnfTsKIGNvbnN0IGFjdHVhbD1rZXlzLm1hcChrZXk9Pntjb25zdCBwcm9kdWN0PXByb2R1Y3RzLmZpbmQocD0+KHAua2V5fHxwLnByb2R1Y3RLZXkpPT09a2V5KTtpZighcHJvZHVjdD8uc291cmNlVXJsKWZhaWwoJ3VudmVyaWZpZWQgcHJvZHVjdCBrZXknKTtyZXR1cm4gcHJvZHVjdC5mYW1pbHl8fG1hcHBpbmdbcHJvZHVjdC5jYXRlZ29yeV07fSk7CiBpZihuZXcgU2V0KGFjdHVhbCkuc2l6ZSE9PWZhbWlsaWVzLmxlbmd0aHx8ZmFtaWxpZXMuc29tZShmPT4hYWN0dWFsLmluY2x1ZGVzKGYpKSlmYWlsKCdwcm9kdWN0IGZhbWlseSBiaW5kaW5nIG1pc21hdGNoJyk7CiBjb25zdCBjbGFpbXM9cmVnaW9uYWxDdXN0b21lckNsYWltcyh0ZXh0KTsKIGZvcihjb25zdCBmYW1pbHkgb2YgY2xhaW1zLmZhbWlsaWVzKWlmKCFmYW1pbGllcy5pbmNsdWRlcyhmYW1pbHkpKWZhaWwoJ21pc3NpbmcgcHJvbWlzZWQgZmFtaWx5ICcrZmFtaWx5KTsKIGlmKG1vZGU9PT0nY29uc3VsdGF0aW9uLW9ubHknJiZjbGFpbXMucHJpY2VPckRlbGl2ZXJ5KWZhaWwoJ2NvbnN1bHRhdGlvbi1vbmx5IHByaWNlL2RlbGl2ZXJ5IHByb21pc2UnKTsKfQoKLyoqIENvbW1vbiBleHBsaWNpdCBjbGFpbXMgb25seTsgaW5kZXBlbmRlbnQgY29udGVudC9zb3VyY2UgcmV2aWV3IHJlbWFpbnMgbWFuZGF0b3J5LiAqLwpleHBvcnQgZnVuY3Rpb24gcmVnaW9uYWxDdXN0b21lckNsYWltcyh0ZXh0KSB7CiBjb25zdCBjb21wYWN0PXRleHQubm9ybWFsaXplKCdORktDJykucmVwbGFjZSgvW1xzXHUyMDBiLVx1MjAwZFx1ZmVmZl0rL2csJycpOwogY29uc3QgdGVybXM9e2JvdXF1ZXQ6L+q9g+uLpOuwnHzrtoDsvIAvLGJhc2tldDov6r2D67CU6rWs64uILyxmdW5lcmFsOi8oPzrqt7zsobB87J6l66GAKSg/OlswLTldK+uLqCk/7ZmU7ZmYfOq3vOyhsFvCty/jho1d7LaV7ZWY7ZmU7ZmYLyxjb25ncmF0czovKD867LaV7ZWYfOqwnOyXhSkoPzpbMC05XSvri6gpP+2ZlO2ZmC99OwogY29uc3QgZmFtaWxpZXM9T2JqZWN0LmVudHJpZXModGVybXMpLmZpbHRlcigoWyxwYXR0ZXJuXSk9PnBhdHRlcm4udGVzdChjb21wYWN0KSkubWFwKChbZmFtaWx5XSk9PmZhbWlseSk7CiBjb25zdCBwcmljZT0vKD86WzAtOV0rKD86Wy4sXVswLTldKykqfFvsnbzsnbTsgrzsgqzsmKTsnKHsuaDtjJTqtazsi63rsLHsspzrp4zslrVdKykoPzpb7Iut67Cx7LKc66eM7Ja1XSspP+ybkHwoPzrigql8S1JXKVswLTldL2kudGVzdChjb21wYWN0KTsKIGNvbnN0IG5lZ2F0aXZlPS9eKD867J2EfOulvHzsnbR86rCAfOydgHzripQpPyg/Ou2VmOyngOyVinztlZjsp4Drqrt87ZWg7IiY7JeGfOuQmOyngOyVinzrkJjripTqsoMoPzrsnbR87J2AKT/slYR87JWE64uIfOyVhOuLmXzsl4Z867aI6rCAKS87CiBsZXQgZGVsaXZlcnk9ZmFsc2U7CiBmb3IoY29uc3Qgc2VudGVuY2Ugb2YgY29tcGFjdC5zcGxpdCgvWy4hP+OAgu+8ge+8n1xuXS8pKXsKICBmb3IoY29uc3QgbWF0Y2ggb2Ygc2VudGVuY2UubWF0Y2hBbGwoL+ustOujjCg/OuuwsOyGoXzrsLDri6wpfOuwsOyGoeu5hOustOujjC9nKSlpZighbmVnYXRpdmUudGVzdChzZW50ZW5jZS5zbGljZShtYXRjaC5pbmRleCttYXRjaFswXS5sZW5ndGgpKSlkZWxpdmVyeT10cnVlOwogIGlmKC/rsLDshqF867Cw64usfOuPhOywqS8udGVzdChzZW50ZW5jZSkpZm9yKGNvbnN0IG1hdGNoIG9mIHNlbnRlbmNlLm1hdGNoQWxsKC/rs7TsnqV87ZmV7JW9L2cpKWlmKCFuZWdhdGl2ZS50ZXN0KHNlbnRlbmNlLnNsaWNlKG1hdGNoLmluZGV4K21hdGNoWzBdLmxlbmd0aCkpKWRlbGl2ZXJ5PXRydWU7CiB9CiByZXR1cm4ge2ZhbWlsaWVzLHByaWNlT3JEZWxpdmVyeTpwcmljZXx8ZGVsaXZlcnl9Owp9CgpleHBvcnQgY29uc3QgcmVnaW9uYWxNZXRhZGF0YUZpZWxkcz1bJ3Njb3BlS2V5JywncmVnaW9uVW5pdEtleXMnLCdyZWdpb25hbFB1cmNoYXNlTW9kZScsJ3JlZ2lvbmFsUHJvZHVjdEtleXMnLCdyZWdpb25hbFByb2R1Y3RGYW1pbGllcycsJ29nSW1hZ2UnLCdvZ0ltYWdlQWx0Jywnb2dJbWFnZVNoYTI1NicsJ29nSW1hZ2VTb3VyY2VVcmwnLCdvZ0ltYWdlV2lkdGgnLCdvZ0ltYWdlSGVpZ2h0Jywnb2dJbWFnZVR5cGUnXTsKLyoqIEFsbCBkZXJpdmVkIGZpZWxkcyBjb21lIGZyb20gdGhlIGV4aXN0aW5nIHJldmlld2VkIHNvdXJjZSBiaW5kaW5nLCBuZXZlciBhbiBpbXBsaWNpdCBmYWxsYmFjay4gKi8KZXhwb3J0IGZ1bmN0aW9uIHJlZ2lvbmFsTWV0YWRhdGEoY292ZXJhZ2UscG9saWN5LHByb2R1Y3RzLHBhZ2VLZXkpIHsKIGNvbnN0IHI9Y292ZXJhZ2UucmVwcmVzZW50YXRpdmVzLmZpbmQocj0+ci5wYWdlS2V5PT09cGFnZUtleSk7CiBjb25zdCBtYXRjaGVzPShwb2xpY3kudmlzdWFsQmluZGluZ3N8fFtdKS5maWx0ZXIoYT0+YS5wYWdlS2V5PT09cGFnZUtleSksYT1tYXRjaGVzWzBdOwogaWYoIXJ8fG1hdGNoZXMubGVuZ3RoIT09MXx8YS5zdGF0dXMhPT0nYXBwcm92ZWQnfHwhWydicmFuZCcsJ3JlYWxfcHJvZHVjdCddLmluY2x1ZGVzKGEuYXNzZXRUeXBlKXx8IWEudmVyaWZpZWRBdClmYWlsKCdtaXNzaW5nIHJldmlld2VkIGJpbmRpbmcnKTsKIGlmKCFbJ2NhdGFsb2cnLCdjb25zdWx0YXRpb24tb25seSddLmluY2x1ZGVzKGEucHVyY2hhc2VNb2RlKXx8IUFycmF5LmlzQXJyYXkoYS5wcm9kdWN0S2V5cyl8fG5ldyBTZXQoYS5wcm9kdWN0S2V5cykuc2l6ZSE9PWEucHJvZHVjdEtleXMubGVuZ3RoKWZhaWwoJ2ludmFsaWQgcHVyY2hhc2UgYmluZGluZycpOwogaWYoKGEucHVyY2hhc2VNb2RlPT09J2NhdGFsb2cnJiYhYS5wcm9kdWN0S2V5cy5sZW5ndGgpfHwoYS5wdXJjaGFzZU1vZGU9PT0nY29uc3VsdGF0aW9uLW9ubHknJiZhLnByb2R1Y3RLZXlzLmxlbmd0aCkpZmFpbCgncHVyY2hhc2UgbW9kZS9rZXkgYmluZGluZyBtaXNtYXRjaCcpOwogY29uc3QgbWFwcGluZz17ZnVuZXJhbF93cmVhdGg6J2Z1bmVyYWwnLGNvbmdyYXRzX3dyZWF0aDonY29uZ3JhdHMnLGZsb3dlcl9ib3VxdWV0Oidib3VxdWV0JyxmbG93ZXJfYmFza2V0OidiYXNrZXQnfTsKIGNvbnN0IGZhbWlsaWVzPVsuLi5uZXcgU2V0KGEucHJvZHVjdEtleXMubWFwKGtleT0+e2NvbnN0IG1hdGNoZXM9cHJvZHVjdHMuZmlsdGVyKHA9PihwLmtleXx8cC5wcm9kdWN0S2V5KT09PWtleSk7aWYobWF0Y2hlcy5sZW5ndGghPT0xfHwhbWF0Y2hlc1swXS5zb3VyY2VVcmwpZmFpbCgnbWlzc2luZyBleGFjdCBjYXRhbG9nIGJpbmRpbmcnKTtjb25zdCBmYW1pbHk9bWF0Y2hlc1swXS5mYW1pbHl8fG1hcHBpbmdbbWF0Y2hlc1swXS5jYXRlZ29yeV07aWYoIVsnYm91cXVldCcsJ2Jhc2tldCcsJ2Z1bmVyYWwnLCdjb25ncmF0cyddLmluY2x1ZGVzKGZhbWlseSkpZmFpbCgnaW52YWxpZCBib3VuZCBmYW1pbHknKTtyZXR1cm4gZmFtaWx5O30pKV07CiBpZighYS5pbWFnZXx8IWEuYWx0fHwhYS5zb3VyY2VVcmx8fCEvXlthLWYwLTldezY0fSQvLnRlc3QoYS5zaGEyNTZ8fCcnKXx8IU51bWJlci5pc0ludGVnZXIoYS53aWR0aCl8fCFOdW1iZXIuaXNJbnRlZ2VyKGEuaGVpZ2h0KXx8TWF0aC5taW4oYS53aWR0aCxhLmhlaWdodCk8MXx8IVsnaW1hZ2UvcG5nJywnaW1hZ2UvanBlZycsJ2ltYWdlL3dlYnAnXS5pbmNsdWRlcyhhLnR5cGUpKWZhaWwoJ2luY29tcGxldGUgaW1hZ2UgYmluZGluZycpOwogcmV0dXJuIHtzY29wZUtleTpwb2xpY3kuc2NvcGVLZXkscmVnaW9uVW5pdEtleXM6ci51bml0S2V5cyxyZWdpb25hbFB1cmNoYXNlTW9kZTphLnB1cmNoYXNlTW9kZSxyZWdpb25hbFByb2R1Y3RLZXlzOmEucHJvZHVjdEtleXMscmVnaW9uYWxQcm9kdWN0RmFtaWxpZXM6ZmFtaWxpZXMsb2dJbWFnZTphLmltYWdlLG9nSW1hZ2VBbHQ6YS5hbHQsb2dJbWFnZVNoYTI1NjphLnNoYTI1NixvZ0ltYWdlU291cmNlVXJsOmEuc291cmNlVXJsLG9nSW1hZ2VXaWR0aDphLndpZHRoLG9nSW1hZ2VIZWlnaHQ6YS5oZWlnaHQsb2dJbWFnZVR5cGU6YS50eXBlfTsKfQpleHBvcnQgZnVuY3Rpb24gYXNzZXJ0UmVnaW9uYWxNZXRhZGF0YShyZWNvcmQsY292ZXJhZ2UscG9saWN5LHByb2R1Y3RzKSB7CiBjb25zdCBleHBlY3RlZD1yZWdpb25hbE1ldGFkYXRhKGNvdmVyYWdlLHBvbGljeSxwcm9kdWN0cyxyZWNvcmQucGFnZUtleSk7CiBmb3IoY29uc3QgZmllbGQgb2YgcmVnaW9uYWxNZXRhZGF0YUZpZWxkcylpZihKU09OLnN0cmluZ2lmeShyZWNvcmRbZmllbGRdKSE9PUpTT04uc3RyaW5naWZ5KGV4cGVjdGVkW2ZpZWxkXSkpZmFpbChgcmV2aWV3ZWQgc291cmNlIGJpbmRpbmcgZHJpZnQgJHtyZWNvcmQucGFnZUtleX06ICR7ZmllbGR9YCk7CiByZXR1cm4gZXhwZWN0ZWQ7Cn0K','base64');
const baseline=await import('data:text/javascript;base64,'+baselineBytes.toString('base64'));

const SITE='seoul-yangcheon-flower-direct';
const SCOPE='seoul-yangcheon-direct-initial-20261012';
const MODE='facility-purchase-context-v1';
const clone=structuredClone;
const contextFields=['facilityKey','purchaseIntentKey','contextKey','intentKey'];
const fixtureOnlyOrigin='https://synthetic-facility.invalid';
function representative(index,unitKey,facilityKey=`fixture-facility-${index+1}`,purchaseIntentKey='funeral-condolence-wreath') {
 const slug=`fixture-context-${index+1}`,contextKey=facilityKey+'|'+purchaseIntentKey;
 return {pageKey:SITE+'-region-'+slug,url:`/regions/${slug}/`,slug,unitKeys:[unitKey],intentKey:'seoul-yangcheon|'+contextKey,primaryKeyword:`Synthetic purchase context ${index+1}`,queryEvidence:'Fixture only; no real demand or source claim.',routeMode:'regional',status:'approved',facilityKey,purchaseIntentKey,contextKey};
}
function makeFixture() {
 const units=Array.from({length:4},(_,i)=>({unitKey:`fixture-unit-${i+1}`,name:`Synthetic legal unit ${i+1}`,unitType:'legal-dong',districtKeys:['synthetic-mapo'],legalRi:[]}));
 const assigned=[units[0],units[0],units[0],units[1],units[2]];
 const coverage={schemaVersion:2,siteKey:SITE,scopeKey:SCOPE,unitBasis:'legal-dong-plus-eup-myeon',countIsPageQuota:false,verifiedAt:'2026-10-11',sourceBasisDate:'2026-10-11',officialSourceUrls:[fixtureOnlyOrigin+'/membership'],districts:[{key:'synthetic-mapo',name:'Synthetic district',sourceUrl:fixtureOnlyOrigin+'/membership'}],units,administrativeCrosswalk:[
  {aliasKey:'synthetic-admin-one',name:'Synthetic admin one',districtKey:'synthetic-mapo',relations:[{unitKey:units[0].unitKey,scope:'partial'},{unitKey:units[1].unitKey,scope:'whole'}]},
  {aliasKey:'synthetic-admin-two',name:'Synthetic admin two',districtKey:'synthetic-mapo',relations:[{unitKey:units[0].unitKey,scope:'partial'},{unitKey:units[2].unitKey,scope:'whole'},{unitKey:units[3].unitKey,scope:'whole'}]},
 ],representativeAssignment:MODE,facilities:assigned.map((unit,i)=>({facilityKey:`fixture-facility-${i+1}`,name:`Synthetic facility ${i+1}`,sourceUrl:`${fixtureOnlyOrigin}/facilities/${i+1}`,address:`Synthetic Road ${i+1}`,unitKey:unit.unitKey})),representatives:assigned.map((unit,i)=>representative(i,unit.unitKey))};
 const policy={schemaVersion:1,siteKey:SITE,scopeKey:SCOPE,enabled:true,officialHosts:['synthetic-facility.invalid'],unitTypes:['legal-dong'],representativeAssignment:MODE,visualBindings:[]};
 return {coverage,policy,products:[],pages:[],architecture:{siteKey:SITE,pages:[]}};
}
function materialize(input) {
 const {coverage,policy,products}=input;
 policy.visualBindings=coverage.representatives.map(r=>({pageKey:r.pageKey,image:'/images/synthetic.png',alt:'Synthetic fixture only',sha256:'a'.repeat(64),sourceUrl:fixtureOnlyOrigin+'/asset',assetType:'brand',width:1200,height:630,type:'image/png',verifiedAt:'2026-10-11',purchaseMode:'consultation-only',productKeys:[],status:'approved'}));
 input.pages=coverage.representatives.filter(r=>r.status==='approved').map(r=>({pageKey:r.pageKey,url:r.url,slug:r.slug,primaryKeyword:r.primaryKeyword,category:'regions',pageType:'regional-service',routeType:'category',status:'approved',approvalVerified:true,snapshotId:'synthetic-'+r.slug,snapshotHash:'b'.repeat(64),...runtime.regionalMetadata(coverage,policy,products,r.pageKey)}));
 input.architecture.pages=input.pages.map(p=>({...clone(p),status:'primary',intentKey:coverage.representatives.find(r=>r.pageKey===p.pageKey).intentKey,pageRole:'REGION_SERVICE_LANDING',parentHub:'/regions/',localizationPolicy:'local-required'}));
 return input;
}
function fixture() {return materialize(makeFixture());}
function definitionFails(mutate,pattern=/Regional service:/) {
 const f=makeFixture();mutate(f);assert.throws(()=>runtime.validateDefinition(f.coverage,f.policy),pattern);
}
function rowsFail(mutate,pattern=/Regional service:/) {
 const f=fixture();mutate(f);assert.throws(()=>runtime.regionalRows(f.pages,f.architecture,f.coverage,f.policy),pattern);
}
function legacyFixture() {
 const f=makeFixture();delete f.coverage.representativeAssignment;delete f.coverage.facilities;delete f.policy.representativeAssignment;
 f.coverage.representatives=f.coverage.units.slice(0,3).map((u,i)=>{
  const r=representative(i,u.unitKey);for(const key of contextFields.slice(0,3))delete r[key];r.intentKey='synthetic-legacy|'+r.slug;return r;
 });
 return materialize(f);
}

test('pristine baseline digest is pinned; metadata field list remains legacy-equivalent',()=>{
 assert.equal(createHash('sha256').update(baselineBytes).digest('hex'),'59421a639f73ab10da4516ce069c8ab46dfa75ac3ad3a660847b8b647e0ed489');
 assert.deepEqual(runtime.regionalMetadataFields,baseline.regionalMetadataFields);
});
test('N5 permits three facilities on one of four legal units without mutating inventory',()=>{
 const f=fixture(),before=JSON.stringify(f.coverage);
 assert.equal(Object.hasOwn(f.policy,'facilities'),false);
 assert.equal(runtime.validateDefinition(f.coverage,f.policy),f.coverage);
 const rows=runtime.regionalRows(f.pages,f.architecture,f.coverage,f.policy);
 assert.equal(rows.length,5);assert.equal(new Set(rows.flatMap(p=>p.regionUnitKeys)).size,3);
 assert.equal(f.coverage.units.length-new Set(rows.flatMap(p=>p.regionUnitKeys)).size,1);
 assert.equal(rows.filter(p=>p.regionUnitKeys[0]==='fixture-unit-1').length,3);
 assert.equal(new Set(['/', '/regions/', ...rows.map(p=>p.url)]).size,7);
 assert.equal(runtime.directoryGroups(f.pages,f.architecture,f.coverage,f.policy)[0].items.length,5);
 assert.equal(runtime.aliasTargets('Synthetic legal unit 1',f.pages,f.architecture,f.coverage,f.policy).length,3);
 assert.deepEqual(runtime.hubState(5,true),{exists:true,indexable:true,menu:true,sitemap:true});
 assert.equal(JSON.stringify(f.coverage),before,'membership, partial relations and registry are immutable');
});
test('one facility accepts two distinct supported purchase intents with exact bindings',()=>{
 const f=makeFixture(),r=f.coverage.representatives[1];
 r.facilityKey=f.coverage.facilities[0].facilityKey;r.purchaseIntentKey='wedding-congrats-wreath';r.contextKey=r.facilityKey+'|'+r.purchaseIntentKey;r.intentKey='seoul-yangcheon|'+r.contextKey;
 materialize(f);assert.equal(runtime.regionalRows(f.pages,f.architecture,f.coverage,f.policy).length,5);
 for(const p of f.pages)assert.doesNotThrow(()=>runtime.assertRegionalMetadata(p,f.coverage,f.policy,f.products));
});
test('all four documented purchase intents are accepted',()=>{
 for(const intent of ['funeral-condolence-wreath','wedding-congrats-wreath','opening-congrats-wreath','event-congrats-wreath']){
  const f=makeFixture(),r=f.coverage.representatives[0];r.purchaseIntentKey=intent;r.contextKey=r.facilityKey+'|'+intent;r.intentKey='seoul-yangcheon|'+r.contextKey;
  assert.doesNotThrow(()=>runtime.validateDefinition(f.coverage,f.policy));
 }
});
test('shared official listing URL is valid for distinct normalized addresses',()=>{
 const f=makeFixture();for(const a of f.coverage.facilities)a.sourceUrl=fixtureOnlyOrigin+'/shared-list.pdf';
 assert.doesNotThrow(()=>runtime.validateDefinition(f.coverage,f.policy));
});
test('N10 with one reserved context publishes nine rows and preserves original ten representatives',()=>{
 const f=makeFixture();for(let i=0;i<5;i++)f.coverage.representatives.push(representative(i+5,f.coverage.representatives[i].unitKeys[0],f.coverage.facilities[i].facilityKey,'event-congrats-wreath'));
 f.coverage.representatives[9].status='reserved';materialize(f);
 assert.equal(runtime.regionalRows(f.pages,f.architecture,f.coverage,f.policy).length,9);assert.equal(f.coverage.representatives.length,10);
 assert.equal(new Set(f.coverage.representatives.flatMap(r=>r.unitKeys)).size,3);
 assert.equal(f.pages.some(p=>p.pageKey===f.coverage.representatives[9].pageKey),false);
});
test('legacy unique-unit fixtures retain exact return values and metadata with no new fields',()=>{
 const f=legacyFixture();
 assert.deepEqual(runtime.validateDefinition(clone(f.coverage),clone(f.policy)),baseline.validateDefinition(clone(f.coverage),clone(f.policy)));
 assert.deepEqual(runtime.regionalRows(f.pages,f.architecture,f.coverage,f.policy),baseline.regionalRows(f.pages,f.architecture,f.coverage,f.policy));
 assert.deepEqual(runtime.directoryGroups(f.pages,f.architecture,f.coverage,f.policy),baseline.directoryGroups(f.pages,f.architecture,f.coverage,f.policy));
 assert.deepEqual(runtime.aliasTargets('Synthetic legal unit 1',f.pages,f.architecture,f.coverage,f.policy),baseline.aliasTargets('Synthetic legal unit 1',f.pages,f.architecture,f.coverage,f.policy));
 for(const r of f.coverage.representatives){
  assert.deepEqual(runtime.regionalMetadata(f.coverage,f.policy,[],r.pageKey),baseline.regionalMetadata(f.coverage,f.policy,[],r.pageKey));
  assert.deepEqual(runtime.assertRegionalMetadata(f.pages.find(p=>p.pageKey===r.pageKey),f.coverage,f.policy,[]),baseline.assertRegionalMetadata(f.pages.find(p=>p.pageKey===r.pageKey),f.coverage,f.policy,[]));
 }
});
test('legacy still rejects repeated units and N greater than available unique units',()=>{
 for(const moreThanUnits of [false,true]){
  const f=legacyFixture();if(moreThanUnits)f.coverage.representatives.push({...clone(f.coverage.representatives[0]),pageKey:'extra-one',slug:'extra-one',url:'/regions/extra-one/',intentKey:'extra-one',primaryKeyword:'Extra one'},{...clone(f.coverage.representatives[0]),pageKey:'extra-two',slug:'extra-two',url:'/regions/extra-two/',intentKey:'extra-two',primaryKeyword:'Extra two'});else f.coverage.representatives[1].unitKeys=[f.coverage.representatives[0].unitKeys[0]];
  for(const adapter of [runtime,baseline])assert.throws(()=>adapter.validateDefinition(f.coverage,f.policy),/duplicate\/unknown canonical unit/);
 }
});
test('legacy baseline approval, URL, source, purchase and metadata guards retain matching results',()=>{
 const mutations=[f=>f.coverage.countIsPageQuota=true,f=>f.coverage.officialSourceUrls=['http://synthetic-facility.invalid/x'],f=>f.coverage.representatives[0].unitKeys=['unknown'],f=>f.coverage.representatives[0].url='/wrong/',f=>f.coverage.representatives[1].pageKey=f.coverage.representatives[0].pageKey,f=>f.coverage.administrativeCrosswalk[0].relations[0].scope='invalid'];
 for(const mutate of mutations){const f=legacyFixture();mutate(f);for(const adapter of [runtime,baseline])assert.throws(()=>adapter.validateDefinition(f.coverage,f.policy));}
 const f=legacyFixture(),p=f.pages[0];
 for(const adapter of [runtime,baseline]){assert.deepEqual(adapter.regionalCustomerClaims('Synthetic plain text'),{families:[],priceOrDelivery:false});assert.doesNotThrow(()=>adapter.validateRegionalPurchase(p,[]));assert.throws(()=>adapter.validateRegionalPurchase({...p,regionalPurchaseMode:'catalog'},[]));}
});
test('canonical context collision is rejected even with unique slug, keyword and pageKey',()=>{
 definitionFails(({coverage})=>{const r=coverage.representatives[1],source=coverage.representatives[0];for(const k of contextFields)r[k]=source[k];},/duplicate\/missing intentKey|canonical facility context/);
 definitionFails(({coverage})=>{coverage.representatives[1].contextKey=coverage.representatives[0].contextKey;},/canonical facility context/);
});
test('duplicate route or keyword identities fail closed',()=>{
 for(const field of ['slug','url','pageKey','primaryKeyword','intentKey'])definitionFails(({coverage})=>{coverage.representatives[1][field]=coverage.representatives[0][field];});
});
test('registry rejects duplicate keys, aliases, inconsistent units and unknown fields',()=>{
 definitionFails(({coverage})=>{coverage.facilities.push({...coverage.facilities[0]});},/facility key/);
 definitionFails(({coverage})=>{coverage.facilities.push({...coverage.facilities[0],address:'Another address',unitKey:coverage.units[1].unitKey});},/facility key/);
 definitionFails(({coverage})=>{coverage.facilities[1].sourceUrl=coverage.facilities[0].sourceUrl;coverage.facilities[1].address=coverage.facilities[0].address;},/source\/address identity/);
 definitionFails(({coverage})=>{coverage.facilities[0].unitKey='unknown-unit';},/unknown facility canonical unit/);
 definitionFails(({coverage})=>{coverage.facilities[0].unexpectedField=true;},/unknown\/missing facility fields/);
 for(const field of ['facilityKey','name','sourceUrl','address','unitKey'])definitionFails(({coverage})=>{delete coverage.facilities[0][field];},/unknown\/missing facility fields/);
});
test('normalized source/address alias guard catches case, port, path, fragment and Unicode whitespace aliases',()=>{
 for(const [left,right] of [
  ['https://synthetic-facility.invalid/','https://SYNTHETIC-FACILITY.invalid:443'],
  ['https://synthetic-facility.invalid/','https://synthetic-facility.invalid/?'],
  ['https://synthetic-facility.invalid/registry','https://synthetic-facility.invalid/registry/#alias'],
  ['https://synthetic-facility.invalid/registry','https://synthetic-facility.invalid/a/../registry'],
  ['https://synthetic-facility.invalid/registry?entry=1#one','https://synthetic-facility.invalid/registry?entry=1#two'],
 ])definitionFails(({coverage})=>{coverage.facilities[0].sourceUrl=left;coverage.facilities[1].sourceUrl=right;coverage.facilities[0].address='Synthetic Road 1';coverage.facilities[1].address='  Synthetic\u00a0Road\u2003１  ';},/source\/address identity/);
});
test('different query strings remain distinct evidence URLs',()=>{
 const f=makeFixture();f.coverage.facilities[0].sourceUrl=fixtureOnlyOrigin+'/registry?id=1';f.coverage.facilities[1].sourceUrl=fixtureOnlyOrigin+'/registry?id=2';f.coverage.facilities[1].address=f.coverage.facilities[0].address;
 assert.doesNotThrow(()=>runtime.validateDefinition(f.coverage,f.policy));
});
test('unknown facilities, unsupported or blank intents and malformed context identifiers are rejected',()=>{
 for(const key of ['',null,'unknown-facility','MixedCase','bad_key','bad|key','bad--key','bad\nkey'])definitionFails(({coverage})=>{coverage.representatives[0].facilityKey=key;});
 for(const intent of ['',null,'funeral','flower-delivery','FUNERAL-CONDOLENCE-WREATH','event|congrats'])definitionFails(({coverage})=>{coverage.representatives[0].purchaseIntentKey=intent;});
 for(const key of ['',null,'Bad-Key','bad_key','bad|key','bad--key','bad\u0000key'])definitionFails(({coverage})=>{coverage.facilities[0].facilityKey=key;});
 for(const field of ['slug','pageKey'])for(const value of ['','bad--key','bad_key','BadKey','bad|key'])definitionFails(({coverage})=>{coverage.representatives[0][field]=value;});
 definitionFails(({coverage})=>{coverage.representatives[0].contextKey='slug-derived-context';});
 definitionFails(({coverage})=>{coverage.representatives[0].intentKey='other-region|'+coverage.representatives[0].contextKey;});
});
test('facility name and address require non-empty normalized text',()=>{
 for(const field of ['name','address'])for(const value of ['', ' \t\n ',null,{},'bad\u0000text','bad\u200btext'])definitionFails(({coverage})=>{coverage.facilities[0][field]=value;});
});
test('unsafe facility source URLs are rejected before WHATWG normalization can sanitize them',()=>{
 const urls=['http://synthetic-facility.invalid/','HTTPS://synthetic-facility.invalid/','https:synthetic-facility.invalid','//synthetic-facility.invalid','https:///synthetic-facility.invalid','https://user:pass@synthetic-facility.invalid/','https://@synthetic-facility.invalid/','https://user@synthetic-facility.invalid/','https://synthetic-facility.invalid\\x','https://synthetic-facility.invalid/with space','https://synthetic-facility.invalid/\npath','https://synthetic-facility.invalid/\tpath','https://synthetic-facility.invalid/\u0000path','https://synthetic-facility.invalid/\u007fpath','https://synthetic-facility.invalid/\u200bpath','https://%73ynthetic-facility.invalid/','https://synthétic.invalid/','https://synthetic-facility.invalid:invalid/','https://127.1/','https://127.0.0.1/','https://0x7f000001/','https://[::1]/','https://localhost/','https://bad_host.invalid/','https://synthetic-facility.invalid/한글','https://synthetic-facility.invalid/?q=한글',...['\"',"'",'<','>','{','}','|','`','^'].map(char=>'https://synthetic-facility.invalid/path'+char),'https://','',null];
 for(const sourceUrl of urls)definitionFails(({coverage})=>{coverage.facilities[0].sourceUrl=sourceUrl;},/facility source URL/);
});
test('unknown, one-sided, absent and wrong-region or wrong-scope opt-ins fail closed',()=>{
 for(const target of ['coverage','policy']){
  definitionFails(f=>{delete f[target].representativeAssignment;},/opt-in mismatch/);
  for(const value of ['',null,'facility-purchase-context-v2',undefined])definitionFails(f=>{f[target].representativeAssignment=value;},/opt-in mismatch/);
 }
 definitionFails(f=>{delete f.coverage.representativeAssignment;delete f.policy.representativeAssignment;},/explicit opt-in/);
 definitionFails(f=>{f.coverage.siteKey=f.policy.siteKey='seoul-other-flower-direct';},/site\/scope/);
 definitionFails(f=>{f.coverage.scopeKey=f.policy.scopeKey='seoul-yangcheon-direct-other';},/site\/scope/);
 definitionFails(f=>{f.policy.scopeKey+='-wrong';},/site\/scope/);
 definitionFails(f=>{delete f.coverage.facilities;},/missing facility registry/);
 definitionFails(f=>{f.coverage.facilities=[];},/missing facility registry/);
});
test('every contextual representative has exactly one known registry-bound unit',()=>{
 for(const value of [[],['unknown-unit'],['fixture-unit-1','fixture-unit-2'],['fixture-unit-1','fixture-unit-1'],'fixture-unit-1',null])definitionFails(({coverage})=>{coverage.representatives[0].unitKeys=value;});
 definitionFails(({coverage})=>{coverage.representatives[0].unitKeys=['fixture-unit-2'];},/canonical unit mismatch/);
 definitionFails(({coverage})=>{coverage.representatives[0].unitKey='fixture-unit-2';},/canonical unit mismatch/);
 definitionFails(({coverage})=>{coverage.facilities[0].unitKey='fixture-unit-2';},/canonical unit mismatch/);
});
test('unknown or changed administrative relations remain invalid',()=>{
 definitionFails(({coverage})=>{coverage.administrativeCrosswalk[0].relations[0].unitKey='unknown-unit';},/invalid alias relation/);
 definitionFails(({coverage})=>{coverage.administrativeCrosswalk[0].relations[0].scope='invented-partial';},/invalid alias relation/);
});
test('page and architecture context, intent, keyword and canonical units cross-bind to representatives',()=>{
 for(const collection of ['pages','architecture'])for(const [field,value] of [
  ['facilityKey','fixture-facility-2'],['purchaseIntentKey','wedding-congrats-wreath'],['contextKey','fixture-facility-2|funeral-condolence-wreath'],['intentKey','seoul-yangcheon|different-context'],['primaryKeyword','Different keyword'],['regionUnitKeys',['fixture-unit-2']],['regionUnitKeys',['fixture-unit-1','fixture-unit-2']],['unitKeys',['fixture-unit-2']],['unitKeys',['fixture-unit-1','fixture-unit-2']],['unitKey','fixture-unit-2'],
 ])rowsFail(f=>{(collection==='pages'?f.pages:f.architecture.pages)[0][field]=value;});
 for(const collection of ['pages','architecture'])for(const field of [...contextFields,'regionUnitKeys'])rowsFail(f=>{delete (collection==='pages'?f.pages:f.architecture.pages)[0][field];});
 rowsFail(f=>{for(const collection of [f.pages,f.architecture.pages])for(const field of contextFields)collection[0][field]=f.coverage.representatives[1][field];},/binding drift|semantic mismatch/);
});
test('approved route omission, duplicate architecture row and reserved publication are rejected',()=>{
 rowsFail(f=>{f.pages.pop();},/approved route parity/);
 rowsFail(f=>{f.architecture.pages.push(clone(f.architecture.pages[0]));},/architecture parity/);
 rowsFail(f=>{f.architecture.pages[0].slug='changed-slug';},/architecture parity/);
 rowsFail(f=>{f.coverage.representatives[0].status='reserved';},/approved route parity/);
 rowsFail(f=>{f.pages[0].approvalVerified=false;},/approval mismatch/);
 rowsFail(f=>{f.policy.enabled=false;},/disabled/);
 rowsFail(f=>{f.architecture.siteKey='other-site';},/architecture site mismatch/);
});
test('metadata readback binds context fields in page-map, manifest and architecture records',()=>{
 const f=fixture();
 for(const label of ['page-map','publish-manifest','architecture']){
  const rows=clone(label==='architecture'?f.architecture.pages:f.pages);
  for(const row of rows)assert.doesNotThrow(()=>runtime.assertRegionalMetadata(row,f.coverage,f.policy,f.products));
  for(const [field,value] of [['facilityKey','fixture-facility-2'],['purchaseIntentKey','opening-congrats-wreath'],['contextKey','different|context'],['intentKey','wrong|intent'],['regionUnitKeys',['fixture-unit-2']],['unitKey','fixture-unit-2'],['unitKeys',['fixture-unit-1','fixture-unit-2']],['primaryKeyword','Changed keyword']]){
   const row=clone(rows[0]);row[field]=value;assert.throws(()=>runtime.assertRegionalMetadata(row,f.coverage,f.policy,f.products),/binding drift/);
  }
 }
});
test('optional singular/plural canonical unit fields are accepted only when equal everywhere',()=>{
 const f=fixture();for(const r of f.coverage.representatives)r.unitKey=r.unitKeys[0];
 for(const p of [...f.pages,...f.architecture.pages]){p.unitKey=p.regionUnitKeys[0];p.unitKeys=[...p.regionUnitKeys];}
 assert.equal(runtime.regionalRows(f.pages,f.architecture,f.coverage,f.policy).length,5);
 for(const p of f.pages)assert.doesNotThrow(()=>runtime.assertRegionalMetadata(p,f.coverage,f.policy,[]));
});

test('catalog families match canonical purchase intent within the exact Yangcheon scope',()=>{
 const products=[{key:'synthetic-funeral',family:'funeral',sourceUrl:fixtureOnlyOrigin+'/funeral'},{key:'synthetic-congrats',family:'congrats',sourceUrl:fixtureOnlyOrigin+'/congrats'},{key:'synthetic-bouquet',family:'bouquet',sourceUrl:fixtureOnlyOrigin+'/bouquet'}];
 for(const intent of ['funeral-condolence-wreath','wedding-congrats-wreath','opening-congrats-wreath','event-congrats-wreath']){
  const expected=intent==='funeral-condolence-wreath'?'funeral':'congrats';
  const page={category:'regions',scopeKey:SCOPE,purchaseIntentKey:intent,regionalPurchaseMode:'catalog',regionalProductKeys:['synthetic-'+expected],regionalProductFamilies:[expected]};
  assert.doesNotThrow(()=>runtime.validateRegionalPurchase(page,products));
  for(const family of ['funeral','congrats','bouquet'].filter(f=>f!==expected))assert.throws(()=>runtime.validateRegionalPurchase({...page,regionalProductKeys:['synthetic-'+family],regionalProductFamilies:[family]},products),/intent\/family mismatch/);
  assert.throws(()=>runtime.validateRegionalPurchase({...page,regionalProductKeys:['synthetic-funeral','synthetic-congrats'],regionalProductFamilies:['funeral','congrats']},products),/intent\/family mismatch/);
 }
 const page={category:'regions',scopeKey:SCOPE,purchaseIntentKey:'unknown-intent',regionalPurchaseMode:'catalog',regionalProductKeys:['synthetic-funeral'],regionalProductFamilies:['funeral']};
 assert.throws(()=>runtime.validateRegionalPurchase(page,products),/unsupported facility purchase intent/);
 for(const adapter of [runtime,baseline])assert.doesNotThrow(()=>adapter.validateRegionalPurchase({...page,scopeKey:'legacy-other-scope'},products));
 assert.doesNotThrow(()=>runtime.validateRegionalPurchase({...page,purchaseIntentKey:'funeral-condolence-wreath',regionalPurchaseMode:'consultation-only',regionalProductKeys:[],regionalProductFamilies:[]},[]));
});

test('N4 fixture preserves five-unit inventory and two distinct facilities on one unit',()=>{
 const f=makeFixture();f.coverage.units.push({...clone(f.coverage.units[3]),unitKey:'fixture-unit-5',name:'Synthetic legal unit 5'});
 f.coverage.administrativeCrosswalk[1].relations.push({unitKey:'fixture-unit-5',scope:'whole'});
 f.coverage.facilities.splice(1,1);f.coverage.representatives.splice(1,1);materialize(f);
 const before=JSON.stringify(f.coverage),rows=runtime.regionalRows(f.pages,f.architecture,f.coverage,f.policy);
 assert.equal(rows.length,4);assert.equal(f.coverage.units.length,5);assert.equal(new Set(rows.flatMap(p=>p.regionUnitKeys)).size,3);
 assert.equal(rows.filter(p=>p.regionUnitKeys[0]==='fixture-unit-1').length,2);
 assert.equal(new Set(['/', '/regions/', ...rows.map(p=>p.url)]).size,6);assert.equal(JSON.stringify(f.coverage),before);
});
