//
//  MainTabBar.swift
//  Codagora
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import SwiftUI

struct MainTabBar: View {
    @Binding var selectedTab: MainTab
    @Binding var isQuickActionPresented: Bool

    private let tabs: [MainTab] = [
        .explore,
        .workspace,
        .home,
        .activity,
        .profile
    ]

    var body: some View {
        HStack(spacing: 4) {
            ForEach(tabs) { tab in
                if tab == .home {
                    homeButton
                } else {
                    tabButton(tab)
                }
            }
        }
        .padding(.horizontal, 8)
        .background(Color("CodagoraCard").opacity(0.95))
//        .overlay(alignment: .top) {
//            HStack(spacing: 0) {
//                Rectangle()
//                    .fill(Color("CodagoraBorder"))
//                    .frame(maxWidth: .infinity)
//                    .frame(height: 0.5)
//
//                Color.clear
//                    .frame(width: 76, height: 0.5)
//
//                Rectangle()
//                    .fill(Color("CodagoraBorder"))
//                    .frame(maxWidth: .infinity)
//                    .frame(height: 0.5)
//            }
//        }
    }

    private func tabButton(
        _ tab: MainTab
    ) -> some View {
        let isSelected = selectedTab == tab

        return Button {
            select(tab)
        } label: {
            VStack(spacing: 5) {
                ZStack {
                    if isSelected {
                        Capsule()
                            .fill(
                                Color("CodagoraBlue")
                                    .opacity(0.12)
                            )
                    }

                    Image(
                        systemName: isSelected
                            ? selectedImage(for: tab)
                            : tab.systemImage
                    )
                    .font(
                        .system(
                            size: 19,
                            weight: isSelected
                                ? .semibold
                                : .regular
                        )
                    )
                    .foregroundStyle(
                        isSelected
                            ? Color("CodagoraBlue")
                            : Color("CodagoraGray")
                    )
                    .padding(.horizontal, 16)
                    .padding(.vertical, 6)
                }
                .fixedSize()

                Text(tab.title)
                    .font(.caption2)
                    .fontWeight(
                        isSelected
                            ? .semibold
                            : .regular
                    )
                    .foregroundStyle(
                        isSelected
                            ? Color("CodagoraBlue")
                            : Color("CodagoraGray")
                    )
            }
            .frame(maxWidth: .infinity)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }

    private var homeButton: some View {
        let isSelected = selectedTab == .home

        return Button {
            select(.home)
        } label: {
            VStack(spacing: 4) {
                ZStack {
                    Circle()
                        .fill(
                            isSelected
                                ? Color("CodagoraBlue")
                                : Color("CodagoraSurface")
                        )

                    if isSelected {
                        Circle()
                            .stroke(
                                Color("CodagoraBlue")
                                    .opacity(0.25),
                                lineWidth: 5
                            )
                            .scaleEffect(1.12)
                    }

                    Image(
                        systemName: isQuickActionPresented
                            ? "xmark"
                            : "house.fill"
                    )
                    .font(
                        .system(
                            size: 21,
                            weight: .semibold
                        )
                    )
                    .foregroundStyle(
                        isSelected
                            ? .white
                            : Color("CodagoraGray")
                    )
                    .rotationEffect(
                        .degrees(
                            isQuickActionPresented
                                ? 90
                                : 0
                        )
                    )
                }
                .frame(width: 56, height: 56)
                .scaleEffect(
                    isSelected
                        ? 1
                        : 0.92
                )
                .shadow(
                    color: isSelected
                        ? Color("CodagoraBlue")
                            .opacity(0.25)
                        : .clear,
                    radius: 8,
                    y: 3
                )

                Text("Home")
                    .font(.caption2)
                    .fontWeight(
                        isSelected
                            ? .semibold
                            : .regular
                    )
                    .foregroundStyle(
                        isSelected
                            ? Color("CodagoraBlue")
                            : Color("CodagoraGray")
                    )
            }
            .frame(maxWidth: .infinity)
            .offset(y: -7)
        }
        .buttonStyle(.plain)
    }

    private func select(
        _ tab: MainTab
    ) {
        if tab == .home {
            if selectedTab == .home {
                withAnimation(
                    .snappy(duration: 0.25)
                ) {
                    isQuickActionPresented.toggle()
                }
            } else {
                isQuickActionPresented = false

                withAnimation(
                    .snappy(duration: 0.25)
                ) {
                    selectedTab = .home
                }
            }

            return
        }

        withAnimation(
            .snappy(duration: 0.25)
        ) {
            isQuickActionPresented = false
            selectedTab = tab
        }
    }

    private func selectedImage(
        for tab: MainTab
    ) -> String {
        switch tab {
        case .home:
            return "house.fill"

        case .explore:
            return "globe"

        case .workspace:
            return "rectangle.3.group.fill"

        case .activity:
            return "sparkles"

        case .profile:
            return "person.crop.circle.fill"
        }
    }
}
