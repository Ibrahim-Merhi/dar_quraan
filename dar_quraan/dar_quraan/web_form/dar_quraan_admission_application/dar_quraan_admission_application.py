import frappe


def get_context(context):
	if (frappe.local.lang or "").lower().startswith("ar"):
		context.introduction_text = """
		<div class="dq-admission-intro">
			<p><strong>مرحبًا بكم في دار القرآن.</strong> يرجى تعبئة أقسام الطلب بدقة، لمساعدة فريق القبول على ترشيح البرنامج الأنسب لكم.</p>
			<p class="dq-form-note">الحقول المعلَّمة بنجمة إلزامية، وتُستخدم بياناتكم حصرًا لدراسة طلب الالتحاق.</p>
		</div>
		"""
	return context
