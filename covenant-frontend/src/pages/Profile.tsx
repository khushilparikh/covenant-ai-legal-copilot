import { Check, KeyRound, Sparkles, User as UserIcon } from "lucide-react";
import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useBilling } from "../context/BillingContext";
import { changePassword, getErrorMessage, updateMyProfile } from "../lib/api";
import { Pill } from "../components/ui";

export default function Profile() {
  const { user, updateUser } = useAuth();
  const { status } = useBilling();

  const [fullName, setFullName] = useState(user?.full_name || "");
  const [companyName, setCompanyName] = useState(user?.company_name || "");
  const [jobTitle, setJobTitle] = useState(user?.job_title || "");
  const [phoneNumber, setPhoneNumber] = useState(user?.phone_number || "");
  const [profileBusy, setProfileBusy] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [profileSaved, setProfileSaved] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordBusy, setPasswordBusy] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSaved, setPasswordSaved] = useState(false);

  if (!user) return null;

  const initials = user.full_name.split(" ").map((s) => s[0]).slice(0, 2).join("").toUpperCase();
  const memberSince = new Date(user.created_at).toLocaleDateString(undefined, { year: "numeric", month: "long" });

  const saveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileError(null);
    setProfileSaved(false);
    setProfileBusy(true);
    try {
      const updated = await updateMyProfile({
        full_name: fullName, company_name: companyName, job_title: jobTitle, phone_number: phoneNumber,
      });
      updateUser(updated);
      setProfileSaved(true);
    } catch (err: any) {
      setProfileError(getErrorMessage(err, "Couldn't save your profile."));
    } finally {
      setProfileBusy(false);
    }
  };

  const savePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError(null);
    setPasswordSaved(false);
    if (newPassword !== confirmPassword) {
      setPasswordError("New password and confirmation don't match.");
      return;
    }
    setPasswordBusy(true);
    try {
      await changePassword(currentPassword, newPassword);
      setPasswordSaved(true);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: any) {
      setPasswordError(getErrorMessage(err, "Couldn't update your password."));
    } finally {
      setPasswordBusy(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto px-8 py-7">
      <div className="max-w-2xl">
        {/* Identity header */}
        <div className="rounded-lg p-6 bg-panel border border-line mb-4 flex items-center gap-4">
          <div className="rounded-full w-14 h-14 flex items-center justify-center text-lg font-semibold bg-brass text-ink shrink-0">
            {initials}
          </div>
          <div className="min-w-0">
            <div className="font-serif text-lg text-ink font-semibold truncate">{user.full_name}</div>
            <div className="text-sm text-slate truncate">{user.email}</div>
            <div className="flex items-center gap-2 mt-2">
              <Pill tone={user.role === "admin" ? "ink" : "slate"}>{user.role}</Pill>
              <Pill tone={user.plan === "premium" ? "amber" : "slate"}>
                {user.plan === "premium" ? "Premium plan" : "Free plan"}
              </Pill>
              <span className="text-xs text-slateLight">Member since {memberSince}</span>
            </div>
          </div>
        </div>

        {/* Usage summary */}
        {status && (
          <div className="rounded-lg p-6 bg-panel border border-line mb-4">
            <h3 className="text-sm font-semibold text-ink mb-3">Usage</h3>
            {status.plan === "premium" ? (
              <div className="flex items-center gap-2 text-sm text-slate">
                <Sparkles size={15} className="text-brass" />
                Unlimited contract uploads on the Premium plan.
              </div>
            ) : (
              <div>
                <div className="flex items-center justify-between text-sm mb-1.5">
                  <span className="text-slate">Contracts uploaded</span>
                  <span className="font-mono font-semibold text-ink">{status.uploads_used} / {status.uploads_limit}</span>
                </div>
                <div className="w-full rounded-full h-2 bg-line overflow-hidden">
                  <div
                    className="h-2 rounded-full"
                    style={{
                      width: `${Math.min(100, Math.round((status.uploads_used / (status.uploads_limit || 30)) * 100))}%`,
                      background: status.limit_reached ? "#B3271E" : "#A9822E",
                    }}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Profile details form */}
        <form onSubmit={saveProfile} className="rounded-lg p-6 bg-panel border border-line mb-4">
          <div className="flex items-center gap-2 mb-4">
            <UserIcon size={16} className="text-brass" />
            <h3 className="text-sm font-semibold text-ink">Profile details</h3>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="text-xs font-medium text-slate">Email</label>
              <input
                value={user.email} disabled
                className="mt-1 w-full rounded-md border border-line px-3 py-2 text-sm bg-paper text-slateLight"
              />
            </div>
            <div className="col-span-2">
              <label className="text-xs font-medium text-slate">Full name</label>
              <input
                value={fullName} onChange={(e) => setFullName(e.target.value)} required
                className="mt-1 w-full rounded-md border border-line px-3 py-2 text-sm outline-none focus:border-brass"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate">Company</label>
              <input
                value={companyName} onChange={(e) => setCompanyName(e.target.value)}
                placeholder="Optional"
                className="mt-1 w-full rounded-md border border-line px-3 py-2 text-sm outline-none focus:border-brass"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate">Job title</label>
              <input
                value={jobTitle} onChange={(e) => setJobTitle(e.target.value)}
                placeholder="Optional"
                className="mt-1 w-full rounded-md border border-line px-3 py-2 text-sm outline-none focus:border-brass"
              />
            </div>
            <div className="col-span-2">
              <label className="text-xs font-medium text-slate">Phone number</label>
              <input
                value={phoneNumber} onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder="Optional"
                className="mt-1 w-full rounded-md border border-line px-3 py-2 text-sm outline-none focus:border-brass"
              />
            </div>
          </div>

          {profileError && <p className="text-xs text-redline mt-3">{profileError}</p>}
          {profileSaved && (
            <p className="text-xs text-greenln mt-3 flex items-center gap-1"><Check size={12} /> Profile updated.</p>
          )}

          <button
            type="submit" disabled={profileBusy}
            className="mt-4 text-sm font-medium px-4 py-2 rounded-md bg-ink text-paper disabled:opacity-60"
          >
            {profileBusy ? "Saving..." : "Save changes"}
          </button>
        </form>

        {/* Password change form */}
        <form onSubmit={savePassword} className="rounded-lg p-6 bg-panel border border-line mb-8">
          <div className="flex items-center gap-2 mb-4">
            <KeyRound size={16} className="text-brass" />
            <h3 className="text-sm font-semibold text-ink">Change password</h3>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="text-xs font-medium text-slate">Current password</label>
              <input
                type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required
                className="mt-1 w-full rounded-md border border-line px-3 py-2 text-sm outline-none focus:border-brass"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate">New password</label>
              <input
                type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required minLength={8}
                className="mt-1 w-full rounded-md border border-line px-3 py-2 text-sm outline-none focus:border-brass"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate">Confirm new password</label>
              <input
                type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required minLength={8}
                className="mt-1 w-full rounded-md border border-line px-3 py-2 text-sm outline-none focus:border-brass"
              />
            </div>
          </div>

          {passwordError && <p className="text-xs text-redline mt-3">{passwordError}</p>}
          {passwordSaved && (
            <p className="text-xs text-greenln mt-3 flex items-center gap-1"><Check size={12} /> Password updated.</p>
          )}

          <button
            type="submit" disabled={passwordBusy}
            className="mt-4 text-sm font-medium px-4 py-2 rounded-md bg-ink text-paper disabled:opacity-60"
          >
            {passwordBusy ? "Updating..." : "Update password"}
          </button>
        </form>
      </div>
    </div>
  );
}
