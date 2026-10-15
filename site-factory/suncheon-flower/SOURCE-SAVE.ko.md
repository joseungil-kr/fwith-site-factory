# 순천 검증 소스 보존

이 경로는 순천 비공개 정적 후보의 검증 소스 저장본입니다. 공개 호스트·배포 설정은 없습니다. 목포 26 → 여수 27 → 순천 28 순서를 유지합니다.

- 앱 작업 디렉터리: candidate/
- 필수 입력: inputs/ 및 candidate/public/images/의 재사용 이미지
- 원본 소스 40파일과 필수 원본 18개의 합집합 51파일, 입력 manifest·UI 검토 2파일, 검증 결과 static-qa.json 1파일을 바이트 그대로 보존했습니다.
- 이 안내 1파일을 더해 저장 대상은 55파일입니다. 원래 소스40파일은 수정하지 않았습니다.

candidate/에서 기존 lockfile 의존성이 준비된 상태로 실행합니다.

    ASTRO_TELEMETRY_DISABLED=1 npm run build
    ASTRO_TELEMETRY_DISABLED=1 npm test

빌드를 먼저 실행합니다. build는 입력 결속, typecheck, Astro 정적 빌드, 생성 HTML 검사를 수행하고 test는 생성된 dist를 검사합니다. evidence/static-qa.json은 출력 폴더를 보존하고 기존 검증 결과를 제공하며 재빌드 시 갱신됩니다.

candidate/README.md는 바이트 정체성을 위해 보존한 원래 휴대용 ZIP 사용 안내입니다. 거기에 적힌 묶음 루트 verify_bundle.py·MANIFEST·reference·기존 dist는 이 최소 소스 저장본의 구성요소가 아닙니다. 이 저장본에서는 위 build/test 명령을 사용합니다. 전체 ZIP은 별도의 suncheon-private-portable-candidate-20261015.zip이며 SHA256은 8f5a0ba5764b5702381578ba757aa02d87890b43bb67c3dfdb4f3655cb2fd5ab입니다.

검증 기준 소스40 tree SHA256: 25442ccde80ae4a547753cd590e5a23daf51e482cd531b1cb3df64ffe8b09abe
검증 기준 출력16 tree SHA256: 63c936640490cae6257f38507c01ebea3b2d2c5f86dac20d6caec725237d6011

실제 브라우저·모바일·HTTP·배포·색인은 별도 검증 대상입니다. noindex는 접근 제어가 아니며 이 저장이 사이트 공개를 뜻하지 않습니다.
