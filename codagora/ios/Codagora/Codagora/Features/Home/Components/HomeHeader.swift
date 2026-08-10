//
//  HomeHeader.swift
//  Codagora
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import SwiftUI

struct HomeHeader: View {
    let onTitleTap: () -> Void

    @State private var isNotificationPresented = false
    @State private var isProfilePresented = false

    var body: some View {
        HStack(spacing: 12) {
            Button {
                onTitleTap()
            } label: {
                HStack(spacing: 8) {
                    Image("AppLogo")
                        .resizable()
                        .scaledToFit()
                        .containerRelativeFrame(.horizontal) { width, _ in
                            width * 0.08
                        }

                    Image("AppTitle")
                        .resizable()
                        .renderingMode(.template)
                        .scaledToFit()
                        .foregroundStyle(Color("CodagoraNavy"))
                        .containerRelativeFrame(.horizontal) { width, _ in
                            width * 0.3
                        }
                }
            }
            .buttonStyle(.plain)

            Spacer()

            notificationButton
            profileButton
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 8)
        .background(Color("CodagoraBackground").opacity(0.9))
    }

    private var notificationButton: some View {
        Button {
            isProfilePresented = false
            isNotificationPresented.toggle()
        } label: {
            ZStack(alignment: .topTrailing) {
                Image(systemName: "bell")
                    .font(
                        .system(
                            size: 18,
                            weight: .semibold
                        )
                    )
                    .foregroundStyle(Color("CodagoraNavy"))
                    .frame(
                        width: 38,
                        height: 38
                    )

                Circle()
                    .fill(Color("CodagoraBlue"))
                    .frame(
                        width: 8,
                        height: 8
                    )
                    .offset(
                        x: -5,
                        y: 5
                    )
            }
        }
        .buttonStyle(.plain)
        .popover(
            isPresented: $isNotificationPresented,
            attachmentAnchor: .rect(.bounds),
            arrowEdge: .top
        ) {
            notificationPopup
                .presentationCompactAdaptation(.popover)
        }
    }

    private var profileButton: some View {
        Button {
            isNotificationPresented = false
            isProfilePresented.toggle()
        } label: {
            ZStack {
                Circle()
                    .fill(Color("CodagoraSurface"))
                    .frame(
                        width: 36,
                        height: 36
                    )

                Image(
                    systemName: "person.crop.circle.fill"
                )
                .font(
                    .system(
                        size: 24,
                        weight: .medium
                    )
                )
                .foregroundStyle(Color("CodagoraNavy"))
            }
            .frame(
                width: 38,
                height: 38
            )
        }
        .buttonStyle(.plain)
        .popover(
            isPresented: $isProfilePresented,
            attachmentAnchor: .rect(.bounds),
            arrowEdge: .top
        ) {
            profilePopup
                .presentationCompactAdaptation(.popover)
        }
    }

    private var notificationPopup: some View {
        VStack(
            alignment: .leading,
            spacing: 14
        ) {
            HStack {
                Text("Notifications")
                    .font(.headline)
                    .foregroundStyle(Color("CodagoraNavy"))

                Spacer()

                Button {
                    isNotificationPresented = false
                } label: {
                    Image(systemName: "xmark")
                        .foregroundStyle(
                            Color("CodagoraSecondaryText")
                        )
                }
                .buttonStyle(.plain)
            }

            Divider()

            ContentUnavailableView {
                Label(
                    "通知はありません",
                    systemImage: "bell"
                )
            }
            .foregroundStyle(
                Color("CodagoraSecondaryText")
            )
        }
        .padding(18)
        .frame(
            width: 300,
            height: 220
        )
        .background(Color("CodagoraCard"))
    }

    private var profilePopup: some View {
        VStack(
            alignment: .leading,
            spacing: 6
        ) {
            Button {
                isProfilePresented = false
            } label: {
                Label(
                    "プロフィール",
                    systemImage: "person"
                )
                .foregroundStyle(Color("CodagoraNavy"))
                .frame(
                    maxWidth: .infinity,
                    alignment: .leading
                )
                .padding(.vertical, 8)
            }

            Button {
                isProfilePresented = false
            } label: {
                Label(
                    "設定",
                    systemImage: "gearshape"
                )
                .foregroundStyle(Color("CodagoraNavy"))
                .frame(
                    maxWidth: .infinity,
                    alignment: .leading
                )
                .padding(.vertical, 8)
            }

            Divider()

            Button(
                role: .destructive
            ) {
                isProfilePresented = false
            } label: {
                Label(
                    "ログアウト",
                    systemImage:
                        "rectangle.portrait.and.arrow.right"
                )
                .frame(
                    maxWidth: .infinity,
                    alignment: .leading
                )
                .padding(.vertical, 8)
            }
        }
        .buttonStyle(.plain)
        .padding(14)
        .frame(width: 230)
        .background(Color("CodagoraCard"))
    }
}
