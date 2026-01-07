```mermaid
flowchart TD
    A[Supervisee enters drop-off point]
    B[Supervisee removes clothing and personal belongings<br/>and places them on X-ray tray]
    C[Supervisee enters search room<br/>X-ray machine moves tray forward for scanning]
    D[Scanning complete<br/>Result displayed on NEC system]
    E[No threat detected.<br/>Supervisee retrieves belongings and puts on clothing]
    F[Supervisee leaves pick-up point<br/>X-ray machine moves tray backward and waits for next supervisee]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
