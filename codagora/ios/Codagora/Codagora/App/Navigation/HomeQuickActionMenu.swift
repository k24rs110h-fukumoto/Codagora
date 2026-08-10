//
//  HomeQuickActionMenu.swift
//  Codagora
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import SwiftUI

struct HomeQuickActionMenu: View {
    let onCreateProject: () -> Void
    let onCreateTask: () -> Void
    let onOpenChat: () -> Void
    let onOpenWorkspace: () -> Void

    var body: some View {
        VStack(spacing: 10) {
            HStack(spacing: 10) {
                actionButton(
                    title: "Project",
                    subtitle: "新規作成",
                    systemImage: "plus.square",
                    action: onCreateProject
                )

                actionButton(
                    title: "Task",
                    subtitle: "新規作成",
                    systemImage: "checkmark.circle",
                    action: onCreateTask
                )
            }

            HStack(spacing: 10) {
                actionButton(
                    title: "Chat",
                    subtitle: "最近の会話",
                    systemImage: "bubble.left.and.bubble.right",
                    action: onOpenChat
                )

                actionButton(
                    title: "Workspace",
                    subtitle: "作成・参加",
                    systemImage: "rectangle.3.group",
                    action: onOpenWorkspace
                )
            }
        }
        .padding(12)
        .background(
            .ultraThinMaterial,
            in: RoundedRectangle(
                cornerRadius: 22,
                style: .continuous
            )
        )
        .overlay {
            RoundedRectangle(
                cornerRadius: 22,
                style: .continuous
            )
            .stroke(
                Color.primary.opacity(0.06),
                lineWidth: 1
            )
        }
        .shadow(
            color: .black.opacity(0.08),
            radius: 16,
            y: 6
        )
        .padding(.horizontal, 18)
    }

    private func actionButton(
        title: String,
        subtitle: String,
        systemImage: String,
        action: @escaping () -> Void
    ) -> some View {
        Button(
            action: action
        ) {
            HStack(spacing: 10) {
                Image(systemName: systemImage)
                    .font(
                        .system(
                            size: 17,
                            weight: .semibold
                        )
                    )
                    .foregroundStyle(
                        Color.accentColor
                    )
                    .frame(
                        width: 34,
                        height: 34
                    )
                    .background(
                        Color.accentColor.opacity(0.1),
                        in: RoundedRectangle(
                            cornerRadius: 10,
                            style: .continuous
                        )
                    )

                VStack(
                    alignment: .leading,
                    spacing: 2
                ) {
                    Text(title)
                        .font(.subheadline)
                        .fontWeight(.semibold)
                        .foregroundStyle(.primary)

                    Text(subtitle)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }

                Spacer(minLength: 0)
            }
            .padding(10)
            .frame(maxWidth: .infinity)
            .background(
                Color.primary.opacity(0.035),
                in: RoundedRectangle(
                    cornerRadius: 14,
                    style: .continuous
                )
            )
        }
        .buttonStyle(.plain)
    }
}
