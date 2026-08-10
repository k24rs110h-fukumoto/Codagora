//
//  SplashView.swift
//  Codagora
//
//  Created by Haruto Fukumoto on 2026/08/01.
//

import SwiftUI

struct SplashView: View {
    @Environment(\.accessibilityReduceMotion) private var accessibilityReduceMotion
    
    let onAnimationFinished: () -> Void
    
    @State private var logoOpacity: Double = 0
    @State private var logoScale: CGFloat = 0.55
    @State private var logoRotation: Double = -90
    
    @State private var titleOpacity: Double = 0
    @State private var titleOffset: CGFloat = 14
    
    @State private var subtitleOpacity: Double = 0
    @State private var subtitleOffset: CGFloat = 8
    
    @State private var splashOpacity: Double = 1
    @State private var hasStartedAnimation: Bool = false
    
    var body: some View {
        ZStack {
            Color(
                red: 246 / 255,
                green: 248 / 255,
                blue: 252 / 255
            )
            .ignoresSafeArea()
            
            VStack(spacing: 22) {
                Image("AppLogo")
                    .resizable()
                    .scaledToFit()
                    .frame(width: 96, height: 96)
                    .opacity(logoOpacity)
                    .scaleEffect(logoScale)
                    .rotationEffect(.degrees(logoRotation))
                
                Image("AppTitle")
                    .resizable()
                    .scaledToFit()
                    .frame(width: 270)
                    .opacity(titleOpacity)
                    .offset(y: titleOffset)
            }
        }
        .opacity(splashOpacity)
        .task {
            guard !hasStartedAnimation else {
                return
            }
            
            hasStartedAnimation = true
            await startAnimation()
        }
    }
    
    @MainActor
    private func startAnimation() async {
        if accessibilityReduceMotion {
            await startReducedMotionAnimation()
            return
        }
        
        withAnimation(
            .spring(
                response: 0.55,
                dampingFraction: 0.7
            )
        ) {
            logoOpacity = 1
            logoScale = 1
            logoRotation = 0
        }
        
        await wait(milliseconds: 450)
        
        withAnimation(
            .easeOut(duration: 0.35)
        ) {
            titleOpacity = 1
            titleOffset = 0
        }
        
        await wait(milliseconds: 150)
        
        withAnimation(
            .easeOut(duration: 0.3)
        ) {
            subtitleOpacity = 1
            subtitleOffset = 0
        }
        
        await wait(milliseconds: 650)
        
        withAnimation(
            .easeInOut(duration: 0.3)
        ) {
            splashOpacity = 0
        }
        
        await wait(milliseconds: 300)
        
        onAnimationFinished()
    }
    
    @MainActor
    private func startReducedMotionAnimation() async {
        logoRotation = 0
        logoScale = 1
        
        withAnimation(
            .easeOut(duration: 0.25)
        ) {
            logoOpacity = 1
            titleOpacity = 1
            subtitleOpacity = 1
            titleOffset = 0
            subtitleOffset = 0
        }
        
        await wait(milliseconds: 900)
        
        withAnimation(
            .easeOut(duration: 0.2)
        ) {
            splashOpacity = 0
        }
        
        await wait(milliseconds: 200)
        
        onAnimationFinished()
    }
    
    private func wait(milliseconds: UInt64) async {
        try? await Task.sleep(
            nanoseconds: milliseconds * 1_000_000
        )
    }
}
