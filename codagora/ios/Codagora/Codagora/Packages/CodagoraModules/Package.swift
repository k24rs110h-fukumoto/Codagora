// swift-tools-version: 6.4
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "CodagoraModules",
    platforms: [.iOS(.v17)],
    products: [
        // Products define the executables and libraries a package produces, making them visible to other packages.
        .library(
            name: "CoreUtilities",
            targets: ["CoreUtilities"]
        ),
        .library(
            name: "CoreNetworking",
            targets: ["CoreNetworking"]
        ),
        .library(
            name: "FeatureAuth",
            targets: ["FeatureAuth"]
        ),
        .library(
            name: "FeatureWorkspace",
            targets: ["FeatureWorkspace"]
        )
    ],
    targets: [
        // Targets are the basic building blocks of a package, defining a module or a test suite.
        // Targets can depend on other targets in this package and products from dependencies.
        .target(
            name: "CoreUtilities",
            swiftSettings: [
                .enableUpcomingFeature("ApproachableConcurrency"),
            ],
        ),
        .target(
            name: "CoreNetworking"
        ),
        .target(
            name: "FeatureAuth",
            dependencies: [
                "CoreNetworking",
                "CoreUtilities"
            ]
        ),
        .target(
            name: "FeatureWorkspace",
            dependencies: [
                "CoreNetworking"
            ]
        ),
        .testTarget(
            name: "CoreUtilitiesTests",
            dependencies: [
                "CoreUtilities"
            ]
        ),
        .testTarget(
            name: "CoreNetworkingTests",
            dependencies: [
                "CoreNetworking"
            ]
        ),
        .testTarget(
            name: "FeatureAuthTests",
            dependencies: [
                "FeatureAuth",
                "CoreNetworking"
            ]
        ),
        .testTarget(
            name: "FeatureWorkspaceTests",
            dependencies: ["FeatureWorkspace"]
        )
    ]
)
