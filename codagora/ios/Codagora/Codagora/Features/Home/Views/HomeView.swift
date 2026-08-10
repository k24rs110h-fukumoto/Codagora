//
//  HomeView.swift
//  Codagora
//
//  Created by Haruto Fukumoto on 2026/07/31.
//

import SwiftUI

struct HomeView: View {
    let scrollToTopTrigger: Int
    
    var body: some View {
        NavigationStack {
            ScrollViewReader { proxy in
                ZStack(alignment: .top) {
                    homeContent

                    HomeHeader {
                        scrollToTop(
                            proxy: proxy
                        )
                    }
                }
                .onChange(of: scrollToTopTrigger) {
                    scrollToTop(proxy: proxy)
                }
            }
            .toolbar(.hidden, for: .navigationBar)
        }
    }

    private var homeContent: some View {
        ScrollView {
            Color.clear
                .frame(height: 0)
                .id(HomeScrollTarget.top)

            LazyVStack(
                alignment: .leading,
                spacing: 28
            ) {
                todaySection
                recentSection
                projectsSection
                recommendationSection
            }
            .padding(.horizontal, 20)
            .padding(.top, 70)
            .padding(.bottom, 32)
        }
        .background(
            Color("CodagoraBackground")
        )
    }

    private func scrollToTop(
        proxy: ScrollViewProxy
    ) {
        withAnimation(
            .snappy(duration: 0.3)
        ) {
            proxy.scrollTo(
                HomeScrollTarget.top,
                anchor: .top
            )
        }
    }

    private enum HomeScrollTarget:
        Hashable
    {
        case top
    }

    private var todaySection: some View {
        VStack(
            alignment: .leading,
            spacing: 12
        ) {
            sectionTitle(
                title: "Today",
                systemImage: "sun.max.fill"
            )

            VStack(
                alignment: .leading,
                spacing: 16
            ) {
                HStack {
                    VStack(
                        alignment: .leading,
                        spacing: 4
                    ) {
                        Text("今日の予定")
                            .font(.headline)
                            .foregroundStyle(
                                Color("CodagoraNavy")
                            )

                        Text("今日やることを確認しましょう")
                            .font(.subheadline)
                            .foregroundStyle(
                                Color("CodagoraSecondaryText")
                            )
                    }

                    Spacer()

                    Image(
                        systemName: "arrow.right"
                    )
                    .font(.caption)
                    .foregroundStyle(
                        Color("CodagoraGray")
                    )
                }

                Divider()
                    .overlay(
                        Color("CodagoraBorder")
                    )

                HStack(spacing: 0) {
                    summaryItem(
                        value: "0",
                        title: "Tasks"
                    )

                    Divider()
                        .overlay(
                            Color("CodagoraBorder")
                        )
                        .frame(height: 36)

                    summaryItem(
                        value: "0",
                        title: "Events"
                    )

                    Divider()
                        .overlay(
                            Color("CodagoraBorder")
                        )
                        .frame(height: 36)

                    summaryItem(
                        value: "0",
                        title: "Updates"
                    )
                }
            }
            .padding(18)
            .background(
                Color("CodagoraCard"),
                in: RoundedRectangle(
                    cornerRadius: 20,
                    style: .continuous
                )
            )
        }
    }

    private var recentSection: some View {
        VStack(
            alignment: .leading,
            spacing: 12
        ) {
            sectionTitle(
                title: "Recent",
                systemImage: "clock.fill"
            )

            Button {
            } label: {
                HStack(spacing: 14) {
                    Image(
                        systemName:
                            "rectangle.3.group.fill"
                    )
                    .font(.system(size: 20))
                    .foregroundStyle(
                        Color("CodagoraBlue")
                    )
                    .frame(
                        width: 44,
                        height: 44
                    )
                    .background(
                        Color("CodagoraBlue")
                            .opacity(0.1),
                        in: RoundedRectangle(
                            cornerRadius: 12,
                            style: .continuous
                        )
                    )

                    VStack(
                        alignment: .leading,
                        spacing: 4
                    ) {
                        Text("最近の作業はありません")
                            .font(.subheadline)
                            .fontWeight(.semibold)
                            .foregroundStyle(
                                Color("CodagoraNavy")
                            )

                        Text(
                            "Workspaceを開くとここに表示されます"
                        )
                        .font(.caption)
                        .foregroundStyle(
                            Color("CodagoraSecondaryText")
                        )
                    }

                    Spacer()

                    Image(
                        systemName: "chevron.right"
                    )
                    .font(.caption)
                    .foregroundStyle(
                        Color("CodagoraGray")
                    )
                }
                .padding(16)
                .background(
                    Color("CodagoraCard"),
                    in: RoundedRectangle(
                        cornerRadius: 18,
                        style: .continuous
                    )
                )
            }
            .buttonStyle(.plain)
        }
    }

    private var projectsSection: some View {
        VStack(
            alignment: .leading,
            spacing: 12
        ) {
            HStack {
                sectionTitle(
                    title: "Projects",
                    systemImage:
                        "shippingbox.fill"
                )

                Spacer()

                Button("すべて見る") {
                }
                .font(.caption)
                .foregroundStyle(
                    Color("CodagoraBlue")
                )
            }

            ScrollView(
                .horizontal,
                showsIndicators: false
            ) {
                HStack(spacing: 12) {
                    projectPlaceholder(
                        title: "プロジェクト",
                        subtitle:
                            "参加中のProjectがここに表示されます"
                    )

                    projectPlaceholder(
                        title: "新しいProject",
                        subtitle:
                            "ExploreからProjectを探す"
                    )
                }
            }
            .contentMargins(
                .horizontal,
                0,
                for: .scrollContent
            )
        }
    }

    private var recommendationSection: some View {
        VStack(
            alignment: .leading,
            spacing: 12
        ) {
            sectionTitle(
                title: "Recommendation",
                systemImage: "sparkles"
            )

            VStack(
                alignment: .leading,
                spacing: 12
            ) {
                HStack {
                    Image(
                        systemName: "sparkles"
                    )
                    .foregroundStyle(
                        Color("CodagoraPurple")
                    )

                    Text("Codagoraからのおすすめ")
                        .font(.headline)
                        .foregroundStyle(
                            Color("CodagoraNavy")
                        )

                    Spacer()
                }

                Text(
                    "興味や活動に合わせたProject、Community、Peopleなどをここに表示します。"
                )
                .font(.subheadline)
                .foregroundStyle(
                    Color("CodagoraSecondaryText")
                )

                Button {
                } label: {
                    Text("Exploreを見る")
                        .font(.subheadline)
                        .fontWeight(.semibold)
                        .foregroundStyle(
                            Color("CodagoraBlue")
                        )
                }
                .buttonStyle(.plain)
            }
            .padding(18)
            .background(
                Color("CodagoraCard"),
                in: RoundedRectangle(
                    cornerRadius: 20,
                    style: .continuous
                )
            )
        }
    }

    private func sectionTitle(
        title: String,
        systemImage: String
    ) -> some View {
        HStack(spacing: 7) {
            Image(systemName: systemImage)
                .font(.caption)
                .foregroundStyle(
                    Color("CodagoraBlue")
                )

            Text(title)
                .font(.title3)
                .fontWeight(.bold)
                .foregroundStyle(
                    Color("CodagoraNavy")
                )
        }
    }

    private func summaryItem(
        value: String,
        title: String
    ) -> some View {
        VStack(spacing: 3) {
            Text(value)
                .font(.title3)
                .fontWeight(.bold)
                .foregroundStyle(
                    Color("CodagoraNavy")
                )

            Text(title)
                .font(.caption2)
                .foregroundStyle(
                    Color("CodagoraSecondaryText")
                )
        }
        .frame(maxWidth: .infinity)
    }

    private func projectPlaceholder(
        title: String,
        subtitle: String
    ) -> some View {
        VStack(
            alignment: .leading,
            spacing: 12
        ) {
            RoundedRectangle(
                cornerRadius: 12,
                style: .continuous
            )
            .fill(
                Color("CodagoraBlue")
                    .opacity(0.1)
            )
            .frame(
                width: 40,
                height: 40
            )
            .overlay {
                Image(
                    systemName: "hammer.fill"
                )
                .foregroundStyle(
                    Color("CodagoraBlue")
                )
            }

            Spacer()

            Text(title)
                .font(.headline)
                .foregroundStyle(
                    Color("CodagoraNavy")
                )

            Text(subtitle)
                .font(.caption)
                .foregroundStyle(
                    Color("CodagoraSecondaryText")
                )
                .lineLimit(2)
        }
        .padding(16)
        .frame(
            width: 210,
            height: 150,
            alignment: .leading
        )
        .background(
            Color("CodagoraCard"),
            in: RoundedRectangle(
                cornerRadius: 18,
                style: .continuous
            )
        )
    }
}
