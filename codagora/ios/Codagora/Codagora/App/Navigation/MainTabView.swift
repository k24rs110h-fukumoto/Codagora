//
//  MainTabView.swift
//  Codagora
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import SwiftUI
import FeatureWorkspace

@MainActor
struct MainTabView: View {
    @State private var selectedTab: MainTab = .home
    @State private var isQuickActionPresented = false
    @State private var homeScrollToTopTrigger = 0
    
    @StateObject private var workspaceListViewModel:
    WorkspaceListViewModel
    
    init(
        workspaceListViewModel:
        WorkspaceListViewModel
    ) {
        _workspaceListViewModel = StateObject(
            wrappedValue: workspaceListViewModel
        )
    }
    
    var body: some View {
        TabView(
            selection: $selectedTab
        ) {
            HomeView(
                scrollToTopTrigger: homeScrollToTopTrigger
            )
            .tag(MainTab.home)
            
            ExploreView()
                .tag(MainTab.explore)
            
            WorkspaceView(
                workspaceListViewModel: workspaceListViewModel
            )
            .tag(MainTab.workspace)
            
            ActivityView()
                .tag(MainTab.activity)
            
            ProfileView()
                .tag(MainTab.profile)
        }
        .toolbar(
            .hidden,
            for: .tabBar
        )
        .safeAreaInset(
            edge: .bottom,
            spacing: 0
        ) {
            MainTabBar(
                selectedTab: $selectedTab,
                isQuickActionPresented:
                    $isQuickActionPresented
            )
        }
        .overlay(
            alignment: .bottom
        ) {
            if isQuickActionPresented &&
                selectedTab == .home {
                HomeQuickActionMenu(
                    onCreateProject: {
                        closeQuickAction()
                    },
                    onCreateTask: {
                        closeQuickAction()
                    },
                    onOpenChat: {
                        closeQuickAction()
                    },
                    onOpenWorkspace: {
                        openWorkspace()
                    }
                )
                .padding(
                    .bottom,
                    88
                )
                .transition(
                    .move(edge: .bottom)
                    .combined(
                        with: .opacity
                    )
                )
                .zIndex(10)
            }
        }
        .animation(
            .snappy(duration: 0.28),
            value: isQuickActionPresented
        )
        .onChange(
            of: selectedTab
        ) { _, newValue in
            if newValue != .home {
                isQuickActionPresented = false
            } else {
                homeScrollToTopTrigger += 1
            }
        }
    }
    
    private func closeQuickAction() {
        withAnimation(
            .snappy(duration: 0.28)
        ) {
            isQuickActionPresented = false
        }
    }
    
    private func openWorkspace() {
        withAnimation(
            .snappy(duration: 0.28)
        ) {
            isQuickActionPresented = false
            selectedTab = .workspace
        }
    }
}

// Debug
private struct MockFetchWorkspacesUseCase:
    FetchWorkspacesUseCaseProtocol {
    
    func execute() async throws -> [WorkspaceSummary] {
        []
    }
}

#Preview {
    MainTabView(
        workspaceListViewModel:
            WorkspaceListViewModel(
                fetchWorkspacesUseCase:
                    MockFetchWorkspacesUseCase()
            )
    )
}
