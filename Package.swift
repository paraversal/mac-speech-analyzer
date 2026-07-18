import PackageDescription

let package = Package(
  name: "mac-speech-analyzer",
  platforms: [ .macOS(.v26) ],
  targets: [
    .executableTarget(
      name: "mac-speech-analyzer",
      linkerSettings: [
        .unsafeFlags([
          "-Xlinker","-sectcreate",
          "-Xlinker","__TEXT",
          "-Xlinker","__info_plist",
          "-Xlinker","Info.plist"   
        ])
      ]
    )
  ]
)
