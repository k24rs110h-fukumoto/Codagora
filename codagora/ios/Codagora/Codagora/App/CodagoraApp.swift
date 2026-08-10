//
//  CodagoraApp.swift
//  Codagora
//
//  Created by Haruto Fukumoto on 2026/07/30.
//

import SwiftUI

@main
struct CodagoraApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self)
    private var appDelegate

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
